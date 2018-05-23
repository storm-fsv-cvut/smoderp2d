import arcpy
import arcgisscripting
import shutil
import os
import sys
import numpy as np
from arcpy.sa import *
import math
import csv

import smoderp2d.processes.rainfall as rainfall
import smoderp2d.flow_algorithm.arcgis_dmtfce as arcgis_dmtfce

from smoderp2d import constants

class PrepareData:

# hlavni funkce je prepare_data
    def __init__(self):

        # creating the geoprocessor object
        self.gp = arcgisscripting.create()

        # setting the workspace environment
        self.gp.workspace = self.gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

        # checking arcgis if ArcGIS Spatial extension is available
        arcpy.CheckOutExtension("Spatial") # TODO - raise an exception (21.05.2018 MK)
        self.gp.overwriteoutput = 1

    def addfield(self, input, newfield, datatyp, default_value):  # EDL
        # function for adding fields
        try:
            arcpy.DeleteField_management(input, newfield)
        except:
            pass
        arcpy.AddField_management(input, newfield, datatyp)
        arcpy.CalculateField_management(
            input,
            newfield,
            default_value,
            "PYTHON")
        return input

    def delfield(self,input, field):
        #function for deleting fields
        try:
            arcpy.DeleteField_management(input, newfield) # to je asi chyba ne? spatnej argument (21.05.2018 MK)
        except:
            pass

    def prepare_data(self,args):
    # main function of data_preparation class

        # geoprocessor object
        gp = self.gp

        # get input rasters/shapefile parameters
        dmt = gp.GetParameterAsText(constants.PARAMETER_DMT)
        soil_indata = gp.GetParameterAsText(constants.PARAMETER_SOIL)
        ptyp = gp.GetParameterAsText(constants.PARAMETER_SOIL_TYPE)
        veg_indata = gp.GetParameterAsText(constants.PARAMETER_VEGETATION)
        vtyp = gp.GetParameterAsText(constants.PARAMETER_VEGETATION_TYPE)
        points = gp.GetParameterAsText(constants.PARAMETER_POINTS)

        # rainfall file path and dirname
        rainfall_file_path = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_RAINFALL_FILE)
        dir = os.path.dirname(rainfall_path) # not used

        tab_puda_veg = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE)
        tab_puda_veg_code = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE_CODE)

        end_time = float(gp.GetParameterAsText(constants.PARAMETER_END_TIME)) * 60.0  # prevod na sekundy
        surface_retention = float(gp.GetParameterAsText(constants.PARAMETER_SURFACE_RETENTION)) / 1000  # prevod z [mm] na [m]

        stream = gp.GetParameterAsText(constants.PARAMETER_STREAM)
        tab_stream_tvar = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE)
        tab_stream_tvar_code = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE_CODE)

        # setting output directory as input parameter
        output = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

        # deleting output directory
        shutil.rmtree(output) # why this is after setting workspace and output directory? (21.05.2018 MK)

        if not os.path.exists(output):
            os.makedirs(output)
        arcpy.AddMessage("Creating of the output directory: " + output)
        output_gdb = arcpy.CreateFileGDB_management(output, "results.gdb") # not used

        temp = output + os.sep + "temp"

        if not os.path.exists(temp):
            os.makedirs(temp)

        arcpy.AddMessage("Creating of the temp: " + temp)

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

        if not os.path.exists(temp):
            os.makedirs(temp)

        dmt_copy = temp + os.sep + "dmt_copy"

        arcpy.CopyRaster_management(dmt, dmt_copy)

        arcpy.AddMessage("DMT preparation...")

        dmt_fill, flow_direction, flow_accumulation, slope_orig, copydmt_array, copySlope_array, \
            mat_slope = self.dmt_preparation(dmt_copy, temp)  # zkontrolovat takovehle rozdeleni radku 23.05.2018 MK

        flow_direction_clip, slope_clip, dmt_clip, intersect, sfield, points, null_shp = self.clip_data(gp, temp,
            dmt_copy, veg_indata, soil_indata, vtyp, ptyp, output, points, tab_puda_veg, tab_puda_veg_code, slope_orig,
            flow_direction)

        return boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate, \
            NoDataValue, array_points, \
            cols, rows, combinatIndex, delta_t, \
            mat_pi, mat_ppl, \
            surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_ret, \
            mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
            mat_a, \
            mat_n, \
            output, pixel_area, points, poradi, end_time, spix, state_cell, \
            temp, type_of_computing, vpix, mfda, sr, itera, \
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc

    def dmt_preparation(self, dmt_copy, temp):

        # corners deleting
        dmt_fill, flow_direction, flow_accumulation, slope_orig = arcgis_dmtfce.dmtfce(dmt_copy, temp, "TRUE", "TRUE", "NONE")
        copydmt_array = arcpy.RasterToNumPyArray(dmt_copy)
        copySlope_array = arcpy.RasterToNumPyArray(slope_orig) # not used
        mat_slope = arcpy.RasterToNumPyArray(slope_orig) # not used

        return dmt_fill, flow_direction, flow_accumulation, slope_orig, copydmt_array, copySlope_array, mat_slope

    def clip_data(self, gp, temp, dmt_copy, veg_indata, soil_indata, vtyp, ptyp, output, points, tab_puda_veg,
                  tab_puda_veg_code, slope_orig, flow_direction):
        # TODO: rozdelit na vic podfunkci 23.05.2018 MK

        # adding attribute for soil and vegetation into attribute table (type short int)
        # preparation for clip
        null = temp + os.sep + "hrance_rst"
        null_shp = temp + os.sep + "null.shp"
        arcpy.gp.Reclassify_sa(dmt_copy, "VALUE", "-100000 100000 1", null, "DATA")
        arcpy.RasterToPolygon_conversion(null, null_shp, "NO_SIMPLIFY")

        # add filed for disslolving and masking
        fieldname = "one"
        veg = temp + os.sep + "LandCover.shp"
        soil = temp + os.sep + "Siol_char.shp"
        arcpy.Copy_management(veg_indata, veg)
        arcpy.Copy_management(soil_indata, soil)

        self.addfield(veg, fieldname, "SHORT", 2)
        self.addfield(soil, fieldname, "SHORT", 2)

        soil_boundary = temp + os.sep + "s_b.shp"
        veg_boundary = temp + os.sep + "v_b.shp"

        arcpy.Dissolve_management(veg, veg_boundary, vtyp)
        arcpy.Dissolve_management(soil, soil_boundary, ptyp)

        # mask and clip data
        arcpy.AddMessage("Clip of the source data by intersect")
        grup = [soil_boundary, veg_boundary, null_shp]
        intersect = output + os.sep + "interSoilLU.shp"
        arcpy.Intersect_analysis(grup, intersect, "ALL", "", "INPUT")

        if points and (points != "#") and (points != ""):
            tmpPoints = []
            desc = arcpy.Describe(points)
            shapefieldname = desc.ShapeFieldName
            rows_p = arcpy.SearchCursor(points)
            for row in rows_p:
                fid = row.getValue('FID') # not used
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
                fid = row2.getValue('FID') # not used
                featCheck = row2.getValue(shapefieldnameCheck)
                pntChech = featCheck.getPart()
                tmpPointsCheck.append([pntChech.X, pntChech.Y])
            del rows_pch

            diffpts = [c for c in tmpPoints if c not in tmpPointsCheck]
            if len(diffpts) == 0:
                pass
            else:
                arcpy.AddMessage("!!! Points at coordinates [x,y]:")
                for item in diffpts:
                    arcpy.AddMessage(item)
                arcpy.AddMessage(
                    "are outside the computation domain and will be ingnored !!!")

            points = pointsClipCheck

        arcpy.env.extent = intersect
        soil_clip = temp + os.sep + "soil_clip.shp"
        veg_clip = temp + os.sep + "veg_clip.shp"

        # clipping of the soil and veg data
        arcpy.Clip_analysis(soil, intersect, soil_clip)
        arcpy.Clip_analysis(veg, intersect, veg_clip)
        grup = [soil_clip, veg_clip] # not used
        # intersect = output+os.sep+"prunik.shp"
        # arcpy.Intersect_analysis(grup, intersect, "ALL", "", "INPUT")

        if gp.ListFields(intersect, "puda_veg").Next():
            arcpy.DeleteField_management(intersect, "puda_veg", )
        arcpy.AddField_management(
            intersect,
            "puda_veg",
            "TEXT",
            "",
            "",
            "15",
            "",
            "NULLABLE",
            "NON_REQUIRED",
            "")

        if ptyp == vtyp:
            vtyp1 = vtyp + "_1"
        else:
            vtyp1 = vtyp

        expr = ptyp + vtyp # not used
        fields = [ptyp, vtyp1, "puda_veg"]
        with arcpy.da.UpdateCursor(intersect, fields) as cursor:
            for row in cursor:
                row[2] = row[0] + row[1]
                cursor.updateRow(row)
        del cursor, row

        puda_veg_dbf = temp + os.sep + "puda_veg_tab_current.dbf"

        arcpy.CopyRows_management(tab_puda_veg, puda_veg_dbf)
        sfield = ["k", "s", "n", "pi", "ppl", "ret", "b", "x", "y", "tau", "v"]

        # sfield_txt = "k;s;n;pi;ppl;ret;b;x;y;tau;v"
        arcpy.JoinField_management(
            intersect,
            "puda_veg",
            puda_veg_dbf,
            tab_puda_veg_code,
            "k;s;n;pi;ppl;ret;b;x;y;tau;v")
        # intersect1 = output+"\\puda_vegetace.shp"
        self.delfield(veg, fieldname)
        self.delfield(soil, fieldname)
        # cleaning datatypes - for numpy mud be double
        """for i in sfield:
          inn = i+"n"
          arcpy.AddField_management(intersect, inn, "DOUBLE")
          with arcpy.da.UpdateCursor(intersect, [i, inn]) as tabulka:
            for row in tabulka:
                row[1] = row[0]
                tabulka.updateRow(row)
          arcpy.DeleteField_management(intersect,i)
          arcpy.AddField_management(intersect, i, "DOUBLE")
          with arcpy.da.UpdateCursor(intersect, [i, inn]) as tabulka:
            for rowx in tabulka:
                rowx[0] = rowx[1]
                tabulka.updateRow(row)
          arcpy.DeleteField_management(intersect,inn)
      del row,rowx
      """

        with arcpy.da.SearchCursor(intersect, sfield) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ":
                        arcpy.AddMessage(
                            "Values in soilveg tab are not correct - STOP, check shp file Prunik in output")
                        sys.exit()

        # delta_t = float(gp.GetParameterAsText(constants.PARAMETER_DELTA_T))*60.0
        delta_t = "nechci" # co teda tohle? # 23.05.2018 MK

        # setting progressor
        gp.SetProgressor("default", "Data preparations...") # mrknout na tohle, zatim nevim, co to je a kde by to melo byt 23.05.2018 MK

        # raster description
        dmt_desc = arcpy.Describe(dmt_copy)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # size of cell
        vpix = dmt_desc.MeanCellHeight
        spix = dmt_desc.MeanCellWidth # not used

        maska = temp + os.sep + "maska"
        arcpy.PolygonToRaster_conversion(
            intersect,
            "FID",
            maska,
            "MAXIMUM_AREA",
            cellsize=vpix)

        del vpix, spix, dmt_desc

        # cropping rasters
        dmt_clip = ExtractByMask(dmt_copy, maska)
        dmt_clip.save(output + os.sep + "DTM")
        slope_clip = ExtractByMask(slope_orig, maska)
        slope_clip.save(temp + os.sep + "slope_clip")

        flow_direction_clip = ExtractByMask(flow_direction, maska)
        flow_direction_clip.save(output + os.sep + "flowDir")

        return flow_direction_clip, slope_clip, dmt_clip, intersect, sfield, points, null_shp

    def raster2np(self, dmt_clip, slope_clip, flow_direction_clip, temp, sfield, intersect, points, dmt_fill):
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

        # raster to numpy array conversion
        zeros = []  # k cemu jsou ty nuly? Nevidim nikde vyuziti 23.05.2018 MK
        dmt_array = arcpy.RasterToNumPyArray(dmt_clip)
        zeros.append(dmt_array)
        mat_slope = arcpy.RasterToNumPyArray(slope_clip)
        mat_fd = arcpy.RasterToNumPyArray(flow_direction_clip)

        self.zapis(
            "fl_dir",
            mat_fd,
            x_coordinate,
            y_coordinate,
            spix,
            vpix,
            NoDataValue,
            temp)

        # size of the raster [0] = number of rows; [1] = number of columns
        rows = dmt_array.shape[0]
        cols = dmt_array.shape[1]

        # nasledujici blok by sel urcite napsat lip 23.05.2018 MK
        mat_dmt = dmt_array; zeros.append(mat_dmt)
        mat_k = np.zeros([rows, cols], float); zeros.append(mat_k)
        mat_s = np.zeros([rows, cols], float); zeros.append(mat_s)
        mat_n = np.zeros([rows, cols], float); zeros.append(mat_n)
        mat_ppl = np.zeros([rows, cols], float); zeros.append(mat_ppl)
        mat_pi = np.zeros([rows, cols], float); zeros.append(mat_pi)
        mat_ret = np.zeros([rows, cols], float); zeros.append(mat_ret)
        mat_b = np.zeros([rows, cols], float); zeros.append(mat_b)
        mat_x = np.zeros([rows, cols], float); zeros.append(mat_x)
        mat_y = np.zeros([rows, cols], float); zeros.append(mat_y)
        mat_tau = np.zeros([rows, cols], float); zeros.append(mat_tau)
        mat_v = np.zeros([rows, cols], float); zeros.append(mat_v)
        # prevod = np.zeros([rows,cols],float)
        mat_nan = np.zeros([rows, cols], float); zeros.append(mat_nan)
        # mat_slope = np.zeros([rows,cols],float)
        zeros.append(mat_slope)
        mat_a = np.zeros([rows, cols], float); zeros.append(mat_a)
        mat_aa = np.zeros([rows, cols], float); zeros.append(mat_aa)

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

        i = 0
        for x in sfield:
            d = temp + os.sep + "r" + str(x)
            arcpy.PolygonToRaster_conversion(intersect, str(x), d, "MAXIMUM_AREA", "", vpix)
            all_attrib[i] = arcpy.RasterToNumPyArray(d)
            i = i + 1

        mat_k   = all_attrib[0]
        mat_s   = all_attrib[1]
        mat_n   = all_attrib[2]
        mat_ppl = all_attrib[3]
        mat_pi  = all_attrib[4]
        mat_ret = all_attrib[5]
        mat_b   = all_attrib[6]
        mat_x   = all_attrib[7]
        mat_y   = all_attrib[8]
        mat_tau = all_attrib[9]
        mat_v   = all_attrib[10]

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

        # getting points coordinates from optional input shapefile
        if points and (points != "#") and (points != ""):  # to samy je uz na radku 169, do fce? 23.05.2018 MK
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
            del rows_p, i
        else:
            array_points = None

        # trimming the edge cells
        # convert dmt to array
        mat_dmt_fill = arcpy.RasterToNumPyArray(dmt_fill)
        zeros.append(mat_dmt_fill)
        zeros.append(mat_fd)

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

        # checking for points at the edge of the raster
        if points and points != "#":
            for kyk in range(array_points.shape[0] - 1):
                if array_points[kyk][1] == i and array_points[kyk][2] == j:
                    gp.AddMessage("Point FID = " + str(
                        int(array_points[kyk][0])) + " is at the edge of the raster. This point will not be included in results.")
                    array_points = np.delete(array_points, kyk, 0)

        return

    def par(self):
        # calculating the "a" parameter
        for i in range(rows):
            for j in range(cols):
                slope = mat_slope[i][j]
                par_x = mat_x[i][j]
                par_y = mat_y[i][j]
                if i == 3 and j == 90:
                    cxs = 5

                if par_x == NoDataValue or par_y == NoDataValue or slope == NoDataValue:
                    par_a = NoDataValue
                    par_aa = NoDataValue
                    exp = 0

                elif par_x == NoDataValue or par_y == NoDataValue or slope == 0.0:
                    par_a = 0.0001
                    par_aa = par_a / 100 / mat_n[i][j]
                    exp = 0

                else:
                    exp = np.power(slope, par_y)
                    par_a = par_x * exp
                    par_aa = par_a / 100 / mat_n[i][j]

                mat_a[i][j] = par_a
                mat_aa[i][j] = par_aa

        # critical water level
        arcpy.AddMessage("Computing critical level")
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
                    a = mat_a[i][j]
                    aa = mat_aa[i][j]
                    flux_crit = tau_crit * v_crit
                    exp = 1 / (b - 1)

                    if slope == 0.0:
                        hcrit_tau = hcrit_v = hcrit_flux = 1000

                    else:
                        hcrit_v = np.power(
                            (v_crit / aa),
                            exp)  # h critical from v (10 je kuli jednotkam, bude jinak)
                        hcrit_tau = tau_crit / 98.07 / slope  # h critical from tau
                        hcrit_flux = np.power(
                            (flux_crit / slope / 98.07 / aa),
                            (1 / mat_b[i][j]))  # kontrola jednotek

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

        rhcrit_tau = arcpy.NumPyArrayToRaster(
            mat_hcrit_tau,
            ll_corner,
            spix,
            vpix,
            "#")
        rhcrit_tau.save(temp + os.sep + "hcrit_tau")
        rhcrit_flux = arcpy.NumPyArrayToRaster(
            mat_hcrit_flux,
            ll_corner,
            spix,
            vpix,
            "#")
        rhcrit_flux.save(temp + os.sep + "hcrit_flux")
        rhcrit_v = arcpy.NumPyArrayToRaster(
            mat_hcrit_v,
            ll_corner,
            spix,
            vpix,
            "#")
        rhcrit_v.save(temp + os.sep + "hcrit_v")

        zeros.append(mat_hcrit)

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dmt_clip)
        asppii = Times(asp, pii)
        sinasp = arcpy.sa.Sin(asppii)
        cosasp = arcpy.sa.Cos(asppii)
        sinsklon = arcpy.sa.Abs(sinasp)
        cossklon = arcpy.sa.Abs(cosasp)
        # times1 = arcpy.sa.Times(cossklon, sinsklon)
        times1 = arcpy.sa.Plus(cossklon, sinsklon)
        times1.save(temp + os.sep + "ratio_cell")

        efect_vrst = arcpy.sa.Times(times1, spix)
        efect_vrst.save(temp + os.sep + "efect_vrst")
        mat_efect_vrst = arcpy.RasterToNumPyArray(efect_vrst)
        zeros.append(mat_efect_vrst)

        state_cell = np.zeros([rows, cols], float)
        zeros.append(state_cell)

        def zero(mat_layer, zero_layer, loc_row, loc_cols):
            mat_layer = np.zeros([rows, cols], float)
            for i in range(loc_row):
                for j in range(loc_cols):
                    if zero_layer[i][j] == NoDataValue:
                        mat_layer[i][j] = NoDataValue
                    else:
                        mat_layer[i][j] = mat_layer[i][j]
            return mat_layer
        for zz in zeros:
            zz = zero(zz, mat_nan, rows, cols)

        # dokud neni mfda pripraven je toto zakomentovane
        # mfda = arcpy.GetParameterAsText(constants.PARAMETER_MFDA)  # az se tohle odkomentuje, tak prehodit do
                                                        #  prepare_data a sem to posilat jako argument 23.05.2018 MK
        mfda = False
        sr, itera = rainfall.load_precipitation(rainfall_file_path) # rainfall_file_path je treba dat jako vstup do teto funkce 23.05.2018 MK

        # pokud jsou zadane vsechny vstupy pro vypocet toku
        # toky se pocitaji a type_of_computing je 3
        listin = [stream, tab_stream_tvar, tab_stream_tvar_code]  # stream, tab_stream_tvar, tab_stream_tvar_code sem posilat jako vstup do funkce 23.05.2018 MK
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            type_of_computing = 3
        else:
            pass

        if (type_of_computing == 3) or (type_of_computing == 5):

            arcpy.AddMessage('Stream preparation...')

            import smoderp2d.stream_functions.stream_preparation as sp
            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sp.prepare_streams(
                dmt, dmt_copy, mat_dmt_fill, null_shp,
                mat_nan, mat_fd, vpix,
                spix, rows, cols, ll_corner,
                NoDataValue, self.addfield,
                self.delfield, output, dmt_clip,
                intersect, null_shp, gp)

            arcpy.AddMessage("Stream preparation has finished")
        else:
            toky = None
            cell_stream = None
            mat_tok_usek = None
            # mat_tok = None
            STREAM_RATIO = None
            tokyLoc = None

        boundaryRows, boundaryCols, rrows, rcols, mat_boundary = find_boudary_cells(
            rows, cols, mat_nan, NoDataValue, mfda)

        outletCells = None

        arcpy.AddMessage("Data preparation has been finished")

    def zapis(self, name, array_export, l_x, l_y, spix, vpix, NoDataValue, folder):
        ll_corner = arcpy.Point(l_x, l_y)
        raster = arcpy.NumPyArrayToRaster(
            array_export,
            ll_corner,
            spix,
            vpix,
            NoDataValue)
        raster.save(folder + os.sep + name)
        return raster

    # Identification of cells at the domain boundary
    #  @param r rows
    def find_boudary_cells(r, c, mat_nan, noData, mfda):

        mat_boundary = np.zeros([r, c], float)

        nr = range(r)
        nc = range(c)

        cols = []
        rows = []

        boundaryCols = []
        boundaryRows = []

        for i in nr:
            for j in nc:
                val = mat_nan[i][j]
                if i == 0 or j == 0 or i == (r - 1) or j == (c - 1):
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
                    boundaryRows.append(i)
                    inBoundary = True
                if mat_boundary[i][j] == -99 and inBoundary:
                    oneColBoundary.append(j)

                # if (mat_boundary[i][j]==0.0 or mat_boundary[i][j]==-99) and
                # inDomain == False:
                if (mat_boundary[i][j] == 0.0) and inDomain == False:
                    rows.append(i)
                    inDomain = True
                # if (mat_boundary[i][j]==0.0 or mat_boundary[i][j]==-99) and
                # inDomain == True:
                if (mat_boundary[i][j] == 0.0) and inDomain:
                    oneCol.append(j)

            inDomain = False
            inBoundary = False
            cols.append(oneCol)
            boundaryCols.append(oneColBoundary)

        return boundaryRows, boundaryCols, rows, cols, mat_boundary
