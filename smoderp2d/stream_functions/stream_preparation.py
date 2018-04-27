#!/usr/bin/python
# -*- coding: latin-1 -*-
# SMODERP 2D
# Created by Tomas Edlman, CTU Prague, 2015-2016

# posledni uprava
__author__ = "edlman"
__date__ = "$29.12.2015 18:20:20$"

# INITIAL SETTINGS:
# importing project moduls
import smoderp2d.constants as constants
# import smoderp2d.data_preparation
import smoderp2d.flow_algorithm.arcgis_dmtfce as arcgis_dmtfce


# importing system moduls
import arcpy
import arcgisscripting
import shutil
import os
import sys
import numpy as np
from arcpy.sa import *
import math


import smoderp2d.io_functions.prt as prt


# definice erroru  na urovni modulu
#
class Error(Exception):

    """Base class for exceptions in this module."""
    pass


class ZeroSlopeError(Error):

    """Exception raised for zero slope of a reach.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, fid):
        self.msg = 'Reach FID:' + str(fid) + ' has zero slope.'

    def __str__(self):
        return repr(self.msg)


def prepare_streams(dmt, dmt_copy, mat_dmt_fill, null,
                    mat_nan, mat_fd, vpix,
                    spix, rows, cols, ll_corner,
                    NoDataValue, addfield,
                    delfield, output, dmt_clip,
                    intersect, null_shp, gp):

    # creating the geoprocessor object
    gp = arcgisscripting.create()
    # setting the workspace environment
    gp.workspace = gp.GetParameterAsText(
        constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)
    # Overwriting output
    arcpy.env.overwriteOutput = 1
    # Check extensions
    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("Spatial")

    # SET INPUT:
    # Set input
    stream = gp.GetParameterAsText(constants.PARAMETER_STREAM)

    # dmt = data_preparation.dmt
    # dmt_copy = data_preparation.dmt_copy
    # mat_dmt = data_preparation.mat_dmt_fill
    # mat_nan = data_preparation.mat_nan
    # mat_fd = data_preparation.mat_fd
    # vpix = data_preparation.vpix
    # spix = data_preparation.spix
    # rows = data_preparation.rows
    # cols = data_preparation.cols
    # gp = data_preparation.gp
    # ll_corner = data_preparation.ll_corner
    # NoDataValue = data_preparation.NoDataValue
    # addfield = data_preparation.addfield
    # delfield = data_preparation.delfield
    STREAM_RATIO = 1

    # cropped raster info
    dmt_desc = arcpy.Describe(dmt_copy)
    # lower left corner coordinates
    x_coordinate = dmt_desc.extent.XMin
    y_coordinate = dmt_desc.extent.YMin
    arcpy.env.snapRaster = dmt

    # Set output
    # output = data_preparation.output
    temp_dp = output + os.sep + "temp_dp"
    if not os.path.exists(temp_dp):
        os.makedirs(temp_dp)
    tempgdb_dp = arcpy.CreateFileGDB_management(temp_dp, "temp_dp.gdb")

    # WATER FLOWS ACCORDING DMT:
    # dmt_clip = data_preparation.dmt_clip
    dmt_fill, flow_direction, flow_accumulation, slope = arcgis_dmtfce.dmtfce(
        dmt_clip, temp_dp, "TRUE", "TRUE", "NONE")

    # Setnull
    try:
        setnull = arcpy.sa.SetNull(
            flow_accumulation,
            1,
            "VALUE < 300")  # hodnota value??
        setnull.save(temp_dp + os.sep + "setnull")
    except:
        prt.message(
            "Unexepted error during setnull calculation:",
            sys.exc_info()[0])
        raise

    # Stream to feature
    """try:
      toky_dmt = arcpy.sa.StreamToFeature(setnull, flow_direction, temp_dp+os.sep+"toky_dmt", "SIMPLIFY")
  except:
      prt.message("Unexepted error during stream to future calculation:", sys.exc_info()[0])
      raise"""

    # WATER FLOWS ACCORDING DIBAVOD:
    # Clip
    toky = temp_dp + os.sep + "toky.shp"
    tokyLoc = temp_dp + os.sep + "toky.shp"
    # intersect = data_preparation.intersect
    hranice = temp_dp + os.sep + "hranice.shp"
    # null = data_preparation.null_shp
    hranice = arcpy.Clip_analysis(null, intersect, hranice)
    hranice2 = arcpy.Buffer_analysis(
        hranice,
        temp_dp + os.sep + "hranice2.shp",
        -spix / 3,
        "FULL",
        "ROUND",
        "NONE")
    # hranice2 = hranice

    toky = arcpy.Clip_analysis(stream, hranice2, toky)

    arcpy.DeleteField_management(
        toky,
        ["EX_JH",
         "POZN",
         "PRPROP_Z",
         "IDVT",
         "UTOKJ_ID",
         "UTOKJN_ID",
         "UTOKJN_F"])

    # Feature vertices to points - START
    prt.message("Feature vertices to points - START...")
    start = arcpy.FeatureVerticesToPoints_management(
        toky, temp_dp + os.sep + "start", "START")
    # Feature vertices to points - END
    prt.message("Feature vertices to points - END...")
    end = arcpy.FeatureVerticesToPoints_management(
        toky, temp_dp + os.sep + "end", "END")

    # Extract value to points - END
    prt.message("Extract value to points - END...")
    xxx = temp_dp + os.sep + "end_point"
    end_point = arcpy.sa.ExtractValuesToPoints(
        end, dmt_clip, xxx, "NONE", "VALUE_ONLY")
    # Extract value to points - START
    arcpy.AddMessage("Extract value to points - START...")
    xxx = temp_dp + os.sep + "start_point"
    start_point = arcpy.sa.ExtractValuesToPoints(
        start, dmt_clip, xxx, "NONE", "VALUE_ONLY")

    # Join
    arcpy.JoinField_management(toky, "FID", start_point, "ORIG_FID")
    arcpy.JoinField_management(toky, "FID", end_point, "ORIG_FID")
    arcpy.DeleteField_management(
        toky,
        ["SHAPE_LEN",
         "SHAPE_LENG",
         "SHAPE_LE_1",
         "NAZ_TOK_1",
         "TOK_ID_1",
         "SHAPE_LE_2",
         "SHAPE_LE_3",
         "NAZ_TOK_12",
         "TOK_ID_12",
         "SHAPE_LE_4",
         "ORIG_FID_1"])

    # Flip selected lines
    fc = temp_dp + os.sep + "toky.shp"

    field = ["OBJECTID", "RASTERVALU", "RASTERVA_1"]
    prt.message("Flip lines...")  # mat_tok_usek

    # jj tu se zamkne toky a zustane zamcen...
    toky_t = arcpy.MakeFeatureLayer_management(
        toky, temp_dp + os.sep + "tok_t.shp")

    arcpy.SelectLayerByAttribute_management(
        toky_t,
        "NEW_SELECTION",
        "RASTERVALU < RASTERVA_1")
    arcpy.FlipLine_edit(toky_t)
    # arcpy.DeleteField_management(toky_t,
    # ["RASTERVALU","RASTERVA_1","ORIG_FID","ORIG_FID_1"])
    arcpy.DeleteField_management(
        toky,
        ["RASTERVALU",
         "RASTERVA_1",
         "ORIG_FID",
         "ORIG_FID_1"])

    # Feature vertices to points - START
    prt.message("Feature vertices to points - START...")
    start = arcpy.FeatureVerticesToPoints_management(
        toky, temp_dp + os.sep + "start", "START")
    # Feature vertices to points - END
    prt.message("Feature vertices to points - END...")
    end = arcpy.FeatureVerticesToPoints_management(
        toky, temp_dp + os.sep + "end", "END")
    # Extract value to points - START
    prt.message("Extract value to points - START...")
    start_point_check = arcpy.sa.ExtractValuesToPoints(
        start,
        dmt,
        temp_dp + os.sep + "start_point_check",
        "NONE",
        "VALUE_ONLY")
    arcpy.AddXY_management(start_point_check)
    # Extract value to points - END
    prt.message("Extract value to points - END...")
    end_point_check = arcpy.sa.ExtractValuesToPoints(
        end,
        dmt,
        temp_dp + os.sep + "end_point_check",
        "NONE",
        "VALUE_ONLY")
    arcpy.AddXY_management(end_point_check)

    # Join
    A = arcpy.JoinField_management(toky, "FID", start_point_check, "ORIG_FID")
    B = arcpy.JoinField_management(toky, "FID", end_point_check, "ORIG_FID")
    arcpy.DeleteField_management(
        toky,
        ["NAZ_TOK_1",
         "NAZ_TOK_12",
         "TOK_ID_1",
         "TOK_ID_12"])

    fc = toky
    field = ["FID", "RASTERVALU", "POINT_X", "RASTERVA_1", "POINT_X_1"]

    with arcpy.da.SearchCursor(fc, field) as cursor:
        for row in cursor:
            if row[1] > row[3]:
                continue
            else:
                prt.message("Flip line")
                arcpy.FlipLine_edit(fc)
    addfield(toky, "to_node", "DOUBLE", -9999)

    fc = toky
    field_end = [
        "FID",
        "POINT_X",
        "POINT_Y",
        "POINT_X_1",
        "POINT_Y_1",
        "to_node"]
    field_start = [
        "FID",
        "POINT_X",
        "POINT_Y",
        "POINT_X_1",
        "POINT_Y_1",
        "to_node"]
    with arcpy.da.SearchCursor(fc, field_start) as cursor_start:
        for row in cursor_start:
            a = (row[1], row[2])
            d = row[0]
            with arcpy.da.UpdateCursor(fc, field_end) as cursor_end:
                for row in cursor_end:
                    b = (row[3], row[4])
                    if a == b:
                        row[5] = d
                        cursor_end.updateRow(row)
                    else:
                        row[5] = "-9999"

    arcpy.DeleteField_management(
        toky,
        ["SHAPE_LEN",
         "SHAPE_LE_1",
         "SHAPE_LE_2",
         "SHAPE_LE_3",
         "SHAPE_LE_4",
         "SHAPE_LE_5",
         "SHAPE_LE_6",
         "SHAPE_LE_7",
         "SHAPE_LE_8",
         "SHAPE_LE_9",
         "SHAPE_L_10",
         "SHAPE_L_11",
         "SHAPE_L_12",
         "SHAPE_L_13",
         "SHAPE_L_14"])
    arcpy.DeleteField_management(
        toky, ["ORIG_FID", "ORIG_FID_1", "SHAPE_L_14"])

    stream_rst1 = temp_dp + os.sep + "stream_rst"
    stream_rst = arcpy.PolylineToRaster_conversion(
        toky,
        "FID",
        stream_rst1,
        "MAXIMUM_LENGTH",
        "NONE",
        spix)
    tok_usek = temp_dp + os.sep + "tok_usek"

    arcpy.gp.Reclassify_sa(
        stream_rst,
        "VALUE",
        "NoDataValue 1000",
        tok_usek,
        "DATA")  # jj no data 1000 kdyz in useku bude od 10000
    mat_tok_usek = arcpy.RasterToNumPyArray(
        temp_dp + os.sep + "tok_usek",
        ll_corner,
        cols,
        rows)
    mat_tok = arcpy.RasterToNumPyArray(
        temp_dp + os.sep + "tok_usek",
        ll_corner,
        cols,
        rows)
    # hit = arcpy.NumPyArrayToRaster(mat_tok_usek,ll_corner,spix)
    # hit.save(temp_dp+"\\hit")
    pocet = len(mat_tok_usek)
    e = range(pocet)  # useky toku + posledni NoData

    cell_stream = []
    # cropped raster info
    reclass_desc = arcpy.Describe(tok_usek)
    ReclNoDataValue = reclass_desc.noDataValue
    mat_tok_usek = mat_tok_usek.astype('int16')

    for i in range(rows):
        for j in range(cols):
            if mat_tok_usek[i][j] < 0:
                mat_tok_usek[i][j] = 0
            else:
                mat_tok_usek[i][j] += 1000
                poz = [mat_tok_usek[i][j], i, j]
                cell_stream.append(poz)

    for i in range(rows):
        for j in range(cols):
            if mat_tok[i][j] != 255:
                mat_tok[i][j] = 3
            else:
                continue

    # hit1 = arcpy.NumPyArrayToRaster(mat_tok,ll_corner,spix)
    # hit1.save(temp_dp+"\\hit1")
    mat_nan = arcpy.NumPyArrayToRaster(mat_nan, ll_corner, spix)
    mat_nan.save(temp_dp + os.sep + "mat_nan")
    # kavka - proc se tu uklada tady

    # HYDRAULIKA TOKU
    addfield(toky, "length", "DOUBLE", 0.0)  # (m)
    # addfield(toky,"vegetace","TEXT", "trava") #tabulka pro drsnosti, vstupem
    # bude tabulka suseky toku - tvar a opevneni(vegetace) ci rovnou drsnost
    # na tvrdo?
    addfield(toky, "sklon", "DOUBLE", 0.0)  # (-)
    # addfield(toky,"drsnost","DOUBLE", 0)
    addfield(toky, "V_infl_ce", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V_infl_us", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V_infl", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "Q_outfl", "DOUBLE", 0.0)  # (m3/s)
    addfield(toky, "V_outfl", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V_outfl_tm", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V_zbyt", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V_zbyt_tm", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "V", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "h", "DOUBLE", 0.0)  # (m)
    addfield(toky, "vs", "DOUBLE", 0.0)  # (m/s)
    addfield(toky, "NS", "DOUBLE", 0.0)  # (m)

    addfield(toky, "total_Vic", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "total_Viu", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "max_Q", "DOUBLE", 0.0)  # (m3/s)
    addfield(toky, "max_h", "DOUBLE", 0.0)  # (m)
    addfield(toky, "max_vs", "DOUBLE", 0.0)  # (m/s)
    addfield(toky, "total_Vo", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "total_Vi", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "total_NS", "DOUBLE", 0.0)  # (m3)
    addfield(toky, "total_Vz", "DOUBLE", 0.0)  # (m3)

    # sklon
    fc = toky
    field = [
        "FID",
        "RASTERVALU",
        "RASTERVA_1",
        "sklon",
        "SHAPE@LENGTH",
        "length"]
    with arcpy.da.UpdateCursor(fc, field) as cursor:
        for row in cursor:
            sklon_koryta = (row[1] - row[2]) / row[4]
            if sklon_koryta == 0:
                raise ZeroSlopeError(row(0))
            row[3] = sklon_koryta
            cursor.updateRow(row)
            row[5] = row[4]
            cursor.updateRow(row)
    # tvar koryt
    tab_stream_tvar = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE)
    tab_stream_tvar_code = gp.GetParameterAsText(
        constants.PARAMETER_STREAMTABLE_CODE)

    stream_tvar_dbf = temp_dp + os.sep + "stream_tvar.dbf"
    arcpy.CopyRows_management(tab_stream_tvar, stream_tvar_dbf)
    sfield = ["cislo", "smoderp", "tvar", "b", "m", "drsnost", "Q365"]

    try:
        arcpy.JoinField_management(
            toky,
            tab_stream_tvar_code,
            stream_tvar_dbf,
            tab_stream_tvar_code,
            "cislo;tvar;b;m;drsnost;Q365")
    except:
        arcpy.AddField_management(toky, "smoderp", "TEXT")
        arcpy.CalculateField_management(toky, "smoderp", "0", "PYTHON")
        arcpy.JoinField_management(
            toky,
            tab_stream_tvar_code,
            stream_tvar_dbf,
            tab_stream_tvar_code,
            "cislo;tvar;b;m;drsnost;Q365")

    with arcpy.da.SearchCursor(toky, sfield) as cursor:
        for row in cursor:
            for i in range(len(row)):
                if row[i] == " ":
                    prt.message(
                        "Value in tab_stream_tvar are no correct - STOP, check shp file toky in output")

                    sys.exit()

    fields = arcpy.ListFields(toky)
    # field_names = [field.name for field in fields if field.type !=
    # 'Geometry']
    field_names = [field.name for field in fields]
    toky_tmp = [[] for field in fields]

    for row in arcpy.SearchCursor(toky):
        field_vals = [row.getValue(field) for field in field_names]
        # field_vals
        for i in range(len(field_vals)):
            toky_tmp[i].append(field_vals[i])

    del row

    # all columns names in
    """[u'FID', u'Shape', u'Id', u'Id_1', u'Id_12', u'Id_12_13', u'Id_12_1_14', u'Id_12_1_15', u'RASTERVALU', u'POINT_X', u'POINT_Y', u'Id_12_1_16', u'Id_12_1_17', u'Id_12_1_18', u'RASTERVA_1', u'POINT_X_1', u'POINT_Y_1', u'to_node', u'length', u'sklon', u'V_infl_ce', u'V_infl_us', u'V_infl', u'Q_outfl', u'V_outfl', u'V_outfl_tm', u'V_zbyt', u'V_zbyt_tm', u'V', u'h', u'vs', u'NS', u'total_Vic', u'total_Viu', u'max_Q', u'max_h', u'max_vs', u'total_Vo', u'total_Vi', u'total_NS', u'total_Vz', u'smoderp', u'CISLO', u'TVAR', u'B', u'M', u'DRSNOST', u'Q365']"""

    tokylist = []  # Kubuv vyber
    tokylist.append(toky_tmp[field_names.index('FID')])
    tokylist.append(toky_tmp[field_names.index('POINT_X')])
    tokylist.append(toky_tmp[field_names.index('POINT_Y')])
    tokylist.append(toky_tmp[field_names.index('POINT_X_1')])
    tokylist.append(toky_tmp[field_names.index('POINT_Y_1')])
    tokylist.append(toky_tmp[field_names.index('to_node')])
    tokylist.append(toky_tmp[field_names.index('length')])
    tokylist.append(toky_tmp[field_names.index('sklon')])
    try:
        tokylist.append(toky_tmp[field_names.index('smoderp')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('SMODERP')])
    try:
        tokylist.append(toky_tmp[field_names.index('cislo')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('CISLO')])
    try:
        tokylist.append(toky_tmp[field_names.index('tvar')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('TVAR')])
    try:
        tokylist.append(toky_tmp[field_names.index('b')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('B')])
    try:
        tokylist.append(toky_tmp[field_names.index('m')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('M')])
    try:
        tokylist.append(toky_tmp[field_names.index('drsnost')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('DRSNOST')])
    try:
        tokylist.append(toky_tmp[field_names.index('q365')])
    except ValueError:
        tokylist.append(toky_tmp[field_names.index('Q365')])

    return tokylist, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc
