import shutil
import os
import sys
import numpy as np
import math
import csv

import smoderp2d.processes.rainfall as rainfall
import smoderp2d.stream_functions.stream_preparation as sp

from smoderp2d.providers.base import Logger

# arcpy imports
from arcpy.sa import *
import arcpy
import arcgisscripting
import smoderp2d.flow_algorithm.arcgis_dmtfce as arcgis_dmtfce
import constants # poradi parametru z arcgis tool

class PrepareData:

    def __init__(self):

        # creating the geoprocessor object
        self.gp = arcgisscripting.create()

        # setting the workspace environment
        self.gp.workspace = self.gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

        # checking arcgis if ArcGIS Spatial extension is available
        arcpy.CheckOutExtension("Spatial") # TODO - raise an exception (21.05.2018 MK)
        self.gp.overwriteoutput = 1

    def add_message(self,message):
        # arcpy dependent
        arcpy.AddMessage(message)

    def run(self):
    # main function of data_preparation class

        # geoprocessor object
        gp = self.gp

        # get input parameters
        dmt = gp.GetParameterAsText(constants.PARAMETER_DMT)
        soil_indata = gp.GetParameterAsText(constants.PARAMETER_SOIL)
        ptyp = gp.GetParameterAsText(constants.PARAMETER_SOIL_TYPE)
        veg_indata = gp.GetParameterAsText(constants.PARAMETER_VEGETATION)
        vtyp = gp.GetParameterAsText(constants.PARAMETER_VEGETATION_TYPE)
        rainfall_file_path = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_RAINFALL_FILE)
        maxdt = float(gp.GetParameterAsText(constants.PARAMETER_MAX_DELTA_T))
        end_time = float(gp.GetParameterAsText(constants.PARAMETER_END_TIME)) * 60.0  # prevod na s
        points = gp.GetParameterAsText(constants.PARAMETER_POINTS)
        output = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)
        tab_puda_veg = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE)
        tab_puda_veg_code = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE_CODE)
        stream = gp.GetParameterAsText(constants.PARAMETER_STREAM)
        tab_stream_tvar = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE)
        tab_stream_tvar_code = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE_CODE)

        # deleting output directory
        shutil.rmtree(output)

        if not os.path.exists(output):
            os.makedirs(output)
        self.add_message("Creating of the output directory: " + output)

        self.temp = output + os.sep + "temp"

        if not os.path.exists(self.temp):
            os.makedirs(self.temp)

        self.add_message("Creating of the temp: " + self.temp)

        arcpy.env.snapRaster = dmt
        # deleting content of output directory
        dirList = os.listdir(output)  # arcgis bug - locking shapefiles
        ab = 0
        for fname in dirList:
            if "sr.lock" in fname:
                ab = 1

        if ab == 0:
            contents = [os.path.join(output, i) for i in os.listdir(output)]

            [shutil.rmtree(i) if os.path.isdir(i) else os.unlink(i)
             for i in contents]

        if not os.path.exists(self.temp):
            os.makedirs(self.temp)

        temp_gdb = arcpy.CreateFileGDB_management (self.temp, "tempGDB.gdb")
        dmt_copy = self.temp + os.sep + "tempGDB.gdb" + os.sep + "dmt_copy"

        arcpy.CopyRaster_management(dmt, dmt_copy)

        self.add_message("DMT preparation (addMessage)")
        Logger.info("DMT preparation...")

        dmt_fill, flow_direction, flow_accumulation, slope_orig = arcgis_dmtfce.dmtfce(dmt_copy, self.temp,
                                                                                       "TRUE", "TRUE", "NONE")

        # intersect
        intersect, null_shp, sfield = self.get_intersect(dmt_copy, veg_indata, soil_indata, vtyp, ptyp, output, gp,
                                                         tab_puda_veg, tab_puda_veg_code)

        # clip
        points, flow_direction_clip, slope_clip, dmt_clip = self.clip_data(dmt_copy, intersect, output, points,
                                                                           slope_orig, flow_direction)

        # self.save_raster("fl_dir", mat_fd, x_coordinate, y_coordinate, spix, vpix, NoDataValue, self.temp)

        # raster to numpy array conversion
        dmt_array = self.rst2np(dmt_clip)
        mat_slope = self.rst2np(slope_clip)
        mat_fd = self.rst2np(flow_direction_clip)

        x_coordinate, y_coordinate, NoDataValue, vpix, spix, pixel_area, ll_corner, rows, cols \
            = self.get_raster_dim(dmt_clip, dmt_array)

        # mat_par
        all_attrib, mat_nan, mat_slope, mat_dmt, mat_fd, mat_inf_index, combinatIndex, \
            = self.get_mat_par(vpix, rows, cols, NoDataValue, sfield, intersect, dmt_array, mat_slope, mat_fd)

        array_points = self.get_array_points(gp, points, rows, vpix, spix, x_coordinate, y_coordinate)

        mat_a, mat_aa = self.get_a(all_attrib, rows, cols, mat_slope, NoDataValue)

        mat_hcrit = self.crit_water( all_attrib, rows, cols, mat_slope, NoDataValue, ll_corner, vpix, spix, mat_aa)

        sr, itera = rainfall.load_precipitation(rainfall_file_path)

        mat_efect_vrst = self.slope_dir(dmt_clip, spix)

        mfda = False

        type_of_computing, toky, mat_tok_usek, tokyLoc = self.stream_prep(stream, tab_stream_tvar,
                tab_stream_tvar_code, dmt, null_shp, mat_nan, spix, rows, cols, ll_corner, output, dmt_clip, intersect)

        rrows, rcols = self.find_boundary_cells(rows, cols, mat_nan, NoDataValue)

        mat_n = all_attrib[2]
        mat_ppl = all_attrib[3]
        mat_pi = all_attrib[4]
        mat_ret = all_attrib[5]
        mat_b = all_attrib[6]

        self.add_message("Data preparation has been finished")

        data = {
            'br': None,                          \
            'bc': None,                          \
            'mat_boundary': None,                \
            'rr': rrows,                         \
            'rc': rcols,                         \
            'outletCells': None,                 \
            'xllcorner': x_coordinate,           \
            'yllcorner': y_coordinate,           \
            'NoDataValue': NoDataValue,          \
            'array_points': array_points,        \
            'c': cols,                           \
            'r': rows,                           \
            'combinatIndex': combinatIndex,      \
            'maxdt': maxdt,                     \
            'mat_pi': mat_pi,                    \
            'mat_ppl': mat_ppl,                  \
            'surface_retention': None,           \
            'mat_inf_index': mat_inf_index,      \
            'mat_hcrit': mat_hcrit,              \
            'mat_aa': mat_aa,                    \
            'mat_b': mat_b,                      \
            'mat_reten': mat_ret,                \
            'mat_fd': mat_fd,                    \
            'mat_dmt': mat_dmt,                  \
            'mat_efect_vrst': mat_efect_vrst,    \
            'mat_slope': mat_slope,              \
            'mat_nan': mat_nan,                  \
            'mat_a': mat_a,                      \
            'mat_n': mat_n,                      \
            'outdir': output,              \
            'pixel_area': pixel_area,            \
            'points': None,                      \
            'poradi': None,                      \
            'end_time': end_time,                \
            'spix': None,                        \
            'state_cell': None,                  \
            'temp': self.temp,                        \
            'type_of_computing': type_of_computing,\
            'vpix': None,                        \
            'mfda': mfda,                        \
            'sr': sr,                            \
            'itera': itera,                      \
            'toky': toky,                        \
            'cell_stream': None,          \
            'mat_tok_reach': mat_tok_usek,       \
            'STREAM_RATIO': None,                \
            'toky_loc': tokyLoc
            }

        return data

    def add_field(self, input, newfield, datatype, default_value):  # EDL
        # function for adding fields
        try:
            arcpy.DeleteField_management(input, newfield)
        except:
            pass
        arcpy.AddField_management(input, newfield, datatype)
        arcpy.CalculateField_management(input, newfield, default_value, "PYTHON")
        return input

    def get_intersect(self, dmt_copy, veg_indata, soil_indata, vtyp, ptyp, output, gp, tab_puda_veg, tab_puda_veg_code):
        # adding attribute for soil and vegetation into attribute table (type short int)
        # preparation for clip
        null = self.temp + os.sep + "hrance_rst"
        null_shp = self.temp + os.sep + "null.shp"
        arcpy.gp.Reclassify_sa(dmt_copy, "VALUE", "-100000 100000 1", null, "DATA")  # reklasifikuje se vsechno na 1
        arcpy.RasterToPolygon_conversion(null, null_shp, "NO_SIMPLIFY")

        soil_boundary = self.temp + os.sep + "s_b.shp"
        veg_boundary = self.temp + os.sep + "v_b.shp"

        arcpy.Dissolve_management(veg_indata, veg_boundary, vtyp)
        arcpy.Dissolve_management(soil_indata, soil_boundary, ptyp)

        group = [soil_boundary, veg_boundary, null_shp]
        intersect = output + os.sep + "interSoilLU.shp"
        arcpy.Intersect_analysis(group, intersect, "ALL", "", "INPUT")

        if gp.ListFields(intersect, "puda_veg").Next():
            arcpy.DeleteField_management(intersect, "puda_veg")
        arcpy.AddField_management(intersect, "puda_veg", "TEXT", "", "", "15", "", "NULLABLE", "NON_REQUIRED","")

        if ptyp == vtyp:
            vtyp1 = vtyp + "_1"
        else:
            vtyp1 = vtyp

        fields = [ptyp, vtyp1, "puda_veg"]
        with arcpy.da.UpdateCursor(intersect, fields) as cursor:
            for row in cursor:
                row[2] = row[0] + row[1]
                cursor.updateRow(row)
        del cursor

        puda_veg_dbf = self.temp + os.sep + "puda_veg_tab_current.dbf"

        arcpy.CopyRows_management(tab_puda_veg, puda_veg_dbf)
        sfield = ["k", "s", "n", "pi", "ppl", "ret", "b", "x", "y", "tau", "v"]

        arcpy.JoinField_management(intersect, "puda_veg", puda_veg_dbf,tab_puda_veg_code,"k;s;n;pi;ppl;ret;b;x;y;tau;v")

        with arcpy.da.SearchCursor(intersect, sfield) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ":
                        self.add_message(
                            "Values in soilveg tab are not correct - STOP, check shp file Prunik in output")
                        sys.exit()

        return intersect, null_shp, sfield


    def clip_data(self, dmt_copy, intersect, output, points, slope_orig, flow_direction):

        # mask and clip data
        self.add_message("Clip of the source data by intersect")

        if points and (points != "#") and (points != ""):
            points = self.clip_points(points, output, intersect)

        arcpy.env.extent = intersect

        # raster description
        dmt_desc = arcpy.Describe(dmt_copy)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # size of cell
        vpix = dmt_desc.MeanCellHeight

        maska = self.temp + os.sep + "maska"
        arcpy.PolygonToRaster_conversion(intersect, "FID", maska, "MAXIMUM_AREA", cellsize=vpix)

        # cropping rasters
        dmt_clip = ExtractByMask(dmt_copy, maska)
        dmt_clip.save(output + os.sep + "DMT")
        slope_clip = ExtractByMask(slope_orig, maska)
        slope_clip.save(self.temp + os.sep + "slope_clip")

        flow_direction_clip = ExtractByMask(flow_direction, maska)
        flow_direction_clip.save(output + os.sep + "flowDir")

        return points, flow_direction_clip, slope_clip, dmt_clip

    def clip_points(self, points, output, intersect):
        tmpPoints = []
        desc = arcpy.Describe(points)
        shapefieldname = desc.ShapeFieldName
        rows_p = arcpy.SearchCursor(points)
        for row in rows_p:
            feat = row.getValue(shapefieldname)
            pnt = feat.getPart()
            tmpPoints.append([pnt.X, pnt.Y])
        del rows_p

        pointsClipCheck = output + os.sep + "pointsCheck.shp"
        arcpy.Clip_analysis(points, intersect, pointsClipCheck)

        tmpPointsCheck = []
        descCheck = arcpy.Describe(pointsClipCheck)
        shapefieldnameCheck = descCheck.ShapeFieldName
        rows_pch = arcpy.SearchCursor(pointsClipCheck)
        for row2 in rows_pch:
            featCheck = row2.getValue(shapefieldnameCheck)
            pntChech = featCheck.getPart()
            tmpPointsCheck.append([pntChech.X, pntChech.Y])
        del rows_pch

        diffpts = [c for c in tmpPoints if c not in tmpPointsCheck]
        if len(diffpts) == 0:
            pass
        else:
            self.add_message("!!! Points at coordinates [x,y]:")
            for item in diffpts:
                self.add_message(item)
            self.add_message("are outside the computation domain and will be ignored !!!")

        return pointsClipCheck

    def get_attrib(self, vpix, rows, cols, sfield, intersect):

        mat_k = np.zeros([rows, cols], float)
        mat_s = np.zeros([rows, cols], float)
        mat_n = np.zeros([rows, cols], float)
        mat_ppl = np.zeros([rows, cols], float)
        mat_pi = np.zeros([rows, cols], float)
        mat_ret = np.zeros([rows, cols], float)
        mat_b = np.zeros([rows, cols], float)
        mat_x = np.zeros([rows, cols], float)
        mat_y = np.zeros([rows, cols], float)
        mat_tau = np.zeros([rows, cols], float)
        mat_v = np.zeros([rows, cols], float)

        all_attrib = [
            mat_k,
            mat_s,
            mat_n,
            mat_ppl,
            mat_pi,
            mat_ret,
            mat_b,
            mat_x,
            mat_y,
            mat_tau,
            mat_v]  # parametry, ktere se generuji ze shp

        poradi = 0
        for x in sfield:
            d = self.temp + os.sep + "r" + str(x)
            arcpy.PolygonToRaster_conversion(intersect, str(x), d, "MAXIMUM_AREA", "", vpix)
            all_attrib[poradi] = self.rst2np(d)
            poradi = poradi + 1
        return all_attrib

    def rst2np(self,raster):
        return arcpy.RasterToNumPyArray(raster)

    def get_raster_dim(self,dmt_clip, dmt_array):

        # cropped raster info
        dmt_desc = arcpy.Describe(dmt_clip)
        # lower left corner coordinates
        x_coordinate = dmt_desc.Extent.XMin
        y_coordinate = dmt_desc.Extent.YMin
        NoDataValue = dmt_desc.noDataValue
        vpix = dmt_desc.MeanCellHeight
        spix = dmt_desc.MeanCellWidth
        pixel_area = spix * vpix
        ll_corner = arcpy.Point(x_coordinate, y_coordinate)

        # size of the raster [0] = number of rows; [1] = number of columns
        rows = dmt_array.shape[0]
        cols = dmt_array.shape[1]

        return x_coordinate, y_coordinate, NoDataValue, vpix, spix, pixel_area, ll_corner, rows, cols

    def get_mat_par(self, vpix, rows, cols, NoDataValue, sfield, intersect, dmt_array, mat_slope, mat_fd):

        all_attrib = self.get_attrib(vpix, rows, cols, sfield, intersect)

        mat_dmt = dmt_array
        mat_nan = np.zeros([rows, cols], float)
        mat_k = all_attrib[0]
        mat_s = all_attrib[1]
        mat_inf_index = None
        combinatIndex = None

        infiltration_type = int(0)  # "Phillip"
        if infiltration_type == int(0):  #to se rovna vzdycky ne? nechapu tuhle podminku 23.05.2018 MK
            mat_inf_index = np.zeros([rows, cols], int)
            combinat = []
            combinatIndex = []
            for i in range(rows):
                for j in range(cols):
                    kkk = mat_k[i][j]
                    sss = mat_s[i][j]
                    ccc = [kkk, sss]
                    try:
                        if combinat.index(ccc):
                            mat_inf_index[i][j] = combinat.index(ccc)
                    except:
                        combinat.append(ccc)
                        combinatIndex.append([combinat.index(ccc), kkk, sss, 0])
                        mat_inf_index[i][j] = combinat.index(ccc)

        # vyrezani krajnich bunek, kde byly chyby, je to vyrazeno u sklonu a acc
        i = 0
        j = 0

        # data value vector intersection
        for i in range(rows):
            for j in range(cols):
                x_mat_dmt = mat_dmt[i][j]
                slp = mat_slope[i][j]
                if x_mat_dmt == NoDataValue or slp == NoDataValue:
                    mat_nan[i][j] = NoDataValue
                    mat_slope[i][j] = NoDataValue
                    mat_dmt[i][j] = NoDataValue
                else:
                    mat_nan[i][j] = 0

        return all_attrib, mat_nan, mat_slope, mat_dmt, mat_fd, mat_inf_index, combinatIndex

    def get_array_points(self, gp, points, rows, vpix, spix, x_coordinate, y_coordinate):
        # getting points coordinates from optional input shapefile
        if points and (points != "#") and (points != ""):
            # identify the geometry field
            desc = arcpy.Describe(points)
            shapefieldname = desc.ShapeFieldName
            # create search cursor
            rows_p = arcpy.SearchCursor(points)
            # getting number of points in shapefile
            count = arcpy.GetCount_management(points)  # result
            count = count.getOutput(0)

            # empty array
            array_points = np.zeros([int(count), 5], float)

            i = 0
            # each point is saved into matrix from second row to the end. First row
            # is for maximal value from flow accumulation array
            for row in rows_p:
                # getting points ID
                fid = row.getValue('FID')
                array_points[i][0] = fid
                # create the geometry object 'feat'
                feat = row.getValue(shapefieldname)
                pnt = feat.getPart()
                # position i,j in raster
                array_points[i][1] = rows - ((pnt.Y - y_coordinate) // vpix) - 1  # i
                array_points[i][2] = (pnt.X - x_coordinate) // spix  # j
                # x,y coordinates of current point stored in an array
                array_points[i][3] = pnt.X
                array_points[i][4] = pnt.Y
                i = i + 1

        else:
            array_points = None

        # checking for points at the edge of the raster
        if points and points != "#":
            for kyk in range(array_points.shape[0] - 1):
                if array_points[kyk][1] == i and array_points[kyk][2] == j:
                    gp.AddMessage("Point FID = " + str(
                        int(array_points[kyk][
                                0])) + " is at the edge of the raster. This point will not be included in results.")
                    array_points = np.delete(array_points, kyk, 0)
        return array_points

    def get_a(self,all_attrib, rows, cols, mat_slope, NoDataValue):
        mat_n = all_attrib[2]
        mat_x = all_attrib[7]
        mat_y = all_attrib[8]
        mat_a = np.zeros([rows, cols], float)
        mat_aa = np.zeros([rows, cols], float)

        # calculating the "a" parameter
        for i in range(rows):
            for j in range(cols):
                slope = mat_slope[i][j]
                par_x = mat_x[i][j]
                par_y = mat_y[i][j]

                if par_x == NoDataValue or par_y == NoDataValue or slope == NoDataValue:
                    par_a = NoDataValue
                    par_aa = NoDataValue

                elif par_x == NoDataValue or par_y == NoDataValue or slope == 0.0:
                    par_a = 0.0001
                    par_aa = par_a / 100 / mat_n[i][j]

                else:
                    exp = np.power(slope, par_y)
                    par_a = par_x * exp
                    par_aa = par_a / 100 / mat_n[i][j]

                mat_a[i][j] = par_a
                mat_aa[i][j] = par_aa
        return mat_a, mat_aa

    def crit_water(self, all_attrib, rows, cols, mat_slope, NoDataValue, ll_corner, vpix, spix, mat_aa):

        mat_b = all_attrib[6]
        mat_tau = all_attrib[9]
        mat_v = all_attrib[10]

        # critical water level
        self.add_message("Computing critical level")
        mat_hcrit_tau = np.zeros([rows, cols], float)
        mat_hcrit_v = np.zeros([rows, cols], float)
        mat_hcrit_flux = np.zeros([rows, cols], float)
        mat_hcrit = np.zeros([rows, cols], float)
        for i in range(rows):
            for j in range(cols):
                if mat_slope[i][j] != NoDataValue and mat_tau[i][j] != NoDataValue:
                    slope = mat_slope[i][j]
                    tau_crit = mat_tau[i][j]
                    v_crit = mat_v[i][j]
                    b = mat_b[i][j]
                    aa = mat_aa[i][j]
                    flux_crit = tau_crit * v_crit
                    exp = 1 / (b - 1)

                    if slope == 0.0:
                        hcrit_tau = hcrit_v = hcrit_flux = 1000

                    else:
                        hcrit_v = np.power((v_crit / aa), exp)  # h critical from v
                        hcrit_tau = tau_crit / 98.07 / slope  # h critical from tau
                        hcrit_flux = np.power((flux_crit / slope / 98.07 / aa),(1 / mat_b[i][j]))  # kontrola jednotek

                    mat_hcrit_tau[i][j] = hcrit_tau
                    mat_hcrit_v[i][j] = hcrit_v
                    mat_hcrit_flux[i][j] = hcrit_flux
                    hcrit = min(hcrit_tau, hcrit_v, hcrit_flux)
                    mat_hcrit[i][j] = hcrit
                else:
                    mat_hcrit_tau[i][j] = NoDataValue
                    mat_hcrit_v[i][j] = NoDataValue
                    mat_hcrit_flux[i][j] = NoDataValue
                    mat_hcrit[i][j] = NoDataValue

        rhcrit_tau = arcpy.NumPyArrayToRaster(mat_hcrit_tau, ll_corner, spix, vpix, "#")
        rhcrit_tau.save(self.temp + os.sep + "hcrit_tau")

        rhcrit_flux = arcpy.NumPyArrayToRaster(mat_hcrit_flux, ll_corner, spix, vpix, "#")
        rhcrit_flux.save(self.temp + os.sep + "hcrit_flux")

        rhcrit_v = arcpy.NumPyArrayToRaster(mat_hcrit_v, ll_corner, spix, vpix, "#")
        rhcrit_v.save(self.temp + os.sep + "hcrit_v")

        return mat_hcrit

    def slope_dir(self,dmt_clip, spix):

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dmt_clip)
        asppii = arcpy.sa.Times(asp, pii)
        sinasp = arcpy.sa.Sin(asppii)
        cosasp = arcpy.sa.Cos(asppii)
        sinsklon = arcpy.sa.Abs(sinasp)
        cossklon = arcpy.sa.Abs(cosasp)
        times1 = arcpy.sa.Plus(cossklon, sinsklon)
        times1.save(self.temp + os.sep + "ratio_cell")

        efect_vrst = arcpy.sa.Times(times1, spix)
        efect_vrst.save(self.temp + os.sep + "efect_vrst")
        mat_efect_vrst = self.rst2np(efect_vrst)

        return mat_efect_vrst

    def stream_prep(self, stream, tab_stream_tvar, tab_stream_tvar_code, dmt, null_shp, mat_nan,
                    spix, rows, cols, ll_corner, output, dmt_clip, intersect):

        type_of_computing = 1

        # pocitam vzdy s ryhama
        # pokud jsou zadane vsechny vstupy pro vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [stream, tab_stream_tvar, tab_stream_tvar_code]
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            type_of_computing = 3
        else:
            pass

        if (type_of_computing == 3) or (type_of_computing == 5):

            self.add_message("Stream preparation...")

            toky, mat_tok_usek, tokyLoc = sp.prepare_streams(listin, dmt, null_shp,
                                                             mat_nan, spix, rows, cols, ll_corner, self.add_field,
                                                             output, dmt_clip, intersect)

            self.add_message("Stream preparation has finished")

        else:
            toky = None
            mat_tok_usek = None
            tokyLoc = None

        return type_of_computing, toky, mat_tok_usek, tokyLoc

    def save_raster(self, name, array_export, l_x, l_y, spix, vpix, NoDataValue, folder):
        ll_corner = arcpy.Point(l_x, l_y)
        raster = arcpy.NumPyArrayToRaster(
            array_export,
            ll_corner,
            spix,
            vpix,
            NoDataValue)
        raster.save(folder + os.sep + name)

    def find_boundary_cells(self, rows, cols, mat_nan, noData):
        # Identification of cells at the domain boundary

        mat_boundary = np.zeros([rows, cols], float)

        nr = range(rows)
        nc = range(cols)

        rcols = []
        rrows = []

        for i in nr:
            for j in nc:
                val = mat_nan[i][j]
                if i == 0 or j == 0 or i == (rows - 1) or j == (cols - 1):
                    if val != noData:
                        val = -99
                else:
                    if val != noData:
                        if mat_nan[i - 1][j] == noData or mat_nan[i + 1][j] == noData or mat_nan[i][j - 1] == noData or \
                                        mat_nan[i][j - 1] == noData:
                            val = -99
                        if mat_nan[i - 1][j + 1] == noData or mat_nan[i + 1][j + 1] == noData or mat_nan[i - 1][
                                    j - 1] == noData or mat_nan[i + 1][j - 1] == noData:
                            val = -99
                mat_boundary[i][j] = val

        inDomain = False
        inBoundary = False

        for i in nr:
            oneCol = []
            oneColBoundary = []
            for j in nc:

                if mat_boundary[i][j] == -99 and inBoundary == False:
                    inBoundary = True

                if mat_boundary[i][j] == -99 and inBoundary:
                    oneColBoundary.append(j)

                if (mat_boundary[i][j] == 0.0) and inDomain == False:
                    rrows.append(i)
                    inDomain = True

                if (mat_boundary[i][j] == 0.0) and inDomain:
                    oneCol.append(j)

            inDomain = False
            inBoundary = False
            rcols.append(oneCol)

        return rrows, rcols
