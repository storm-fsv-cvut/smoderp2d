import shutil
import os
import sys
import numpy as np
import math
import csv

import smoderp2d.processes.rainfall as rainfall
import smoderp2d.stream_functions.stream_preparation as sp

# arcpy imports
from arcpy.sa import *
import arcpy
import arcgisscripting
import smoderp2d.flow_algorithm.arcgis_dmtfce as arcgis_dmtfce
from smoderp2d import constants # poradi parametru z arcgis tool

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

    def add_message(self,message):
        # arcpy dependent
        arcpy.AddMessage(message)

    def prepare_data(self):
    # main function of data_preparation class

        # geoprocessor object
        gp = self.gp

        # get input parameters
        dmt = gp.GetParameterAsText(constants.PARAMETER_DMT)
        soil_indata = gp.GetParameterAsText(constants.PARAMETER_SOIL)
        ptyp = gp.GetParameterAsText(constants.PARAMETER_SOIL_TYPE)
        veg_indata = gp.GetParameterAsText(constants.PARAMETER_VEGETATION)
        vtyp = gp.GetParameterAsText(constants.PARAMETER_VEGETATION_TYPE)
        points = gp.GetParameterAsText(constants.PARAMETER_POINTS)
        rainfall_file_path = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_RAINFALL_FILE)
        tab_puda_veg = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE)
        tab_puda_veg_code = gp.GetParameterAsText(constants.PARAMETER_SOILVEGTABLE_CODE)
        end_time = float(gp.GetParameterAsText(constants.PARAMETER_END_TIME)) * 60.0  # prevod na s
        surface_retention = float(gp.GetParameterAsText(constants.PARAMETER_SURFACE_RETENTION)) / 1000  # z [mm] na [m]
        stream = gp.GetParameterAsText(constants.PARAMETER_STREAM)
        tab_stream_tvar = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE)
        tab_stream_tvar_code = gp.GetParameterAsText(constants.PARAMETER_STREAMTABLE_CODE)
        output = gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

        # deleting output directory
        shutil.rmtree(output)

        if not os.path.exists(output):
            os.makedirs(output)
        self.add_message("Creating of the output directory: " + output)

        temp = output + os.sep + "temp"

        if not os.path.exists(temp):
            os.makedirs(temp)

        self.add_message("Creating of the temp: " + temp)

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

        temp_gdb = arcpy.CreateFileGDB_management (temp, "tempGDB.gdb")
        dmt_copy = temp + os.sep + "tempGDB.gdb" + os.sep + "dmt_copy"

        arcpy.CopyRaster_management(dmt, dmt_copy)

        self.add_message("DMT preparation...")

        # corners deleting
        dmt_fill, flow_direction, flow_accumulation, slope_orig = arcgis_dmtfce.dmtfce(dmt_copy, temp,
                                                                                       "TRUE", "TRUE", "NONE")

        # clip
        flow_direction_clip, slope_clip, dmt_clip, intersect, sfield, points, null_shp = self.clip_data(gp, temp,
            dmt_copy, veg_indata, soil_indata, vtyp, ptyp, output, points, tab_puda_veg, tab_puda_veg_code, slope_orig,
            flow_direction)

        # raster2np
        array_points, all_attrib, mat_nan, mat_slope, mat_dmt, mat_dmt_fill, mat_fd, mat_inf_index, \
            combinatIndex, rows, cols, vpix, spix, x_coordinate, y_coordinate, ll_corner, pixel_area, \
            NoDataValue, poradi = self.raster2np(gp, dmt_clip, slope_clip, flow_direction_clip, temp, sfield, intersect, points,
                                         dmt_fill)

        # hcrit, a, aa computing
        mat_hcrit, mat_a, mat_aa = self.par(all_attrib, rows, cols, mat_slope, NoDataValue, ll_corner, vpix, spix, temp)

        mat_efect_vrst, state_cell, mfda, sr, itera = self.contour(dmt_clip, temp, spix, rainfall_file_path,rows,cols)

        # pocitam vzdy s ryhama
        type_of_computing = 1
        # pokud jsou zadane vsechny vstupy pro vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [stream, tab_stream_tvar, tab_stream_tvar_code]
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            type_of_computing = 3
        else:
            pass

        if (type_of_computing == 3) or (type_of_computing == 5):

            self.add_message("Stream preparation...")

            toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sp.prepare_streams(listin, dmt, null_shp,
                mat_nan, spix, rows, cols, ll_corner, self.add_field, output, dmt_clip, intersect)

            self.add_message("Stream preparation has finished")

        else:
            toky = None
            cell_stream = None
            mat_tok_usek = None
            STREAM_RATIO = None
            tokyLoc = None

        boundaryRows, boundaryCols, rrows, rcols, mat_boundary = self.find_boudary_cells(
            rows, cols, mat_nan, NoDataValue, mfda)

        outletCells = None

        delta_t = "nechci"
        mat_n = all_attrib[2]
        mat_ppl = all_attrib[3]
        mat_pi = all_attrib[4]
        mat_ret = all_attrib[5]
        mat_b = all_attrib[6]

        self.add_message("Data preparation has been finished")

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

    def add_field(self, input, newfield, datatyp, default_value):  # EDL
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

    def del_field(self,input, field):
        #function for deleting fields
        try:
            arcpy.DeleteField_management(input, newfield) # to je asi chyba ne? spatnej argument (21.05.2018 MK)
        except:
            pass

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

        self.add_field(veg, fieldname, "SHORT", 2)
        self.add_field(soil, fieldname, "SHORT", 2)

        soil_boundary = temp + os.sep + "s_b.shp"
        veg_boundary = temp + os.sep + "v_b.shp"

        arcpy.Dissolve_management(veg, veg_boundary, vtyp)
        arcpy.Dissolve_management(soil, soil_boundary, ptyp)

        # mask and clip data
        self.add_message("Clip of the source data by intersect")
        grup = [soil_boundary, veg_boundary, null_shp]
        intersect = output + os.sep + "interSoilLU.shp"
        arcpy.Intersect_analysis(grup, intersect, "ALL", "", "INPUT")

        if points and (points != "#") and (points != ""):
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
                self.add_message("are outside the computation domain and will be ingnored !!!")

            points = pointsClipCheck

        arcpy.env.extent = intersect
        soil_clip = temp + os.sep + "soil_clip.shp"
        veg_clip = temp + os.sep + "veg_clip.shp"

        # clipping of the soil and veg data
        arcpy.Clip_analysis(soil, intersect, soil_clip)
        arcpy.Clip_analysis(veg, intersect, veg_clip)

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

        fields = [ptyp, vtyp1, "puda_veg"]
        with arcpy.da.UpdateCursor(intersect, fields) as cursor:
            for row in cursor:
                row[2] = row[0] + row[1]
                cursor.updateRow(row)
        del cursor

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
        self.del_field(veg, fieldname)
        self.del_field(soil, fieldname)

        with arcpy.da.SearchCursor(intersect, sfield) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ":
                        self.add_message(
                            "Values in soilveg tab are not correct - STOP, check shp file Prunik in output")
                        sys.exit()

        # setting progressor
        gp.SetProgressor("default", "Data preparations...") # mrknout na tohle, zatim nevim, co to je a kde by to melo byt 23.05.2018 MK

        # raster description
        dmt_desc = arcpy.Describe(dmt_copy)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # size of cell
        vpix = dmt_desc.MeanCellHeight

        maska = temp + os.sep + "maska"
        arcpy.PolygonToRaster_conversion(
            intersect,
            "FID",
            maska,
            "MAXIMUM_AREA",
            cellsize=vpix)

        # cropping rasters
        dmt_clip = ExtractByMask(dmt_copy, maska)
        dmt_clip.save(output + os.sep + "DTM")
        slope_clip = ExtractByMask(slope_orig, maska)
        slope_clip.save(temp + os.sep + "slope_clip")

        flow_direction_clip = ExtractByMask(flow_direction, maska)
        flow_direction_clip.save(output + os.sep + "flowDir")

        return flow_direction_clip, slope_clip, dmt_clip, intersect, sfield, points, null_shp

    def get_attrib(self, temp, vpix, rows, cols, sfield, intersect):

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
            d = temp + os.sep + "r" + str(x)
            arcpy.PolygonToRaster_conversion(intersect, str(x), d, "MAXIMUM_AREA", "", vpix)
            all_attrib[poradi] = arcpy.RasterToNumPyArray(d)
            poradi = poradi + 1

        return all_attrib, poradi

    def raster2np(self, gp, dmt_clip, slope_clip, flow_direction_clip, temp, sfield, intersect, points, dmt_fill):
        # TODO: rozdelit raster2np do vic podfunkci, polovina veci s tim prevodem nesouvisi 23.05.2018 MK

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
        dmt_array = arcpy.RasterToNumPyArray(dmt_clip)
        mat_slope = arcpy.RasterToNumPyArray(slope_clip)
        mat_fd = arcpy.RasterToNumPyArray(flow_direction_clip)

        self.save_raster(
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

        mat_dmt = dmt_array
        mat_nan = np.zeros([rows, cols], float)

        all_attrib, poradi = self.get_attrib(temp, vpix, rows, cols, sfield, intersect)

        mat_k = all_attrib[0]
        mat_s = all_attrib[1]

        infiltration_type = int(0)  # "Phillip"
        if infiltration_type == int(0):  #to se rovna vzdycky ne? nechapu tuhle podminku 23.05.2018 MK
            mat_inf_index = np.zeros([rows, cols], int)
            combinat = []
            combinatIndex = []
            for i in range(rows):  # tady to chce jeste nejak prepsat ty ccc, sss, kkk 23.05.2018 MK
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

        # trimming the edge cells
        # convert dmt to array
        mat_dmt_fill = arcpy.RasterToNumPyArray(dmt_fill)

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

        return array_points, all_attrib, mat_nan, mat_slope, mat_dmt, mat_dmt_fill, mat_fd, mat_inf_index, \
            combinatIndex, rows, cols, vpix, spix, x_coordinate, y_coordinate, ll_corner, pixel_area, \
            NoDataValue, poradi

    def par(self, all_attrib, rows, cols, mat_slope, NoDataValue, ll_corner, vpix, spix, temp):

        mat_n = all_attrib[2]
        mat_b = all_attrib[6]
        mat_x = all_attrib[7]
        mat_y = all_attrib[8]
        mat_tau = all_attrib[9]
        mat_v = all_attrib[10]
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
        rhcrit_tau.save(temp + os.sep + "hcrit_tau")

        rhcrit_flux = arcpy.NumPyArrayToRaster(mat_hcrit_flux, ll_corner, spix, vpix, "#")
        rhcrit_flux.save(temp + os.sep + "hcrit_flux")

        rhcrit_v = arcpy.NumPyArrayToRaster(mat_hcrit_v, ll_corner, spix, vpix, "#")
        rhcrit_v.save(temp + os.sep + "hcrit_v")

        return mat_hcrit, mat_a, mat_aa

    def contour(self,dmt_clip, temp, spix, rainfall_file_path,rows,cols):

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dmt_clip)
        asppii = arcpy.sa.Times(asp, pii)
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

        state_cell = np.zeros([rows, cols], float)

        # dokud neni mfda pripraven je toto zakomentovane
        # mfda = arcpy.GetParameterAsText(constants.PARAMETER_MFDA)  # az se tohle odkomentuje, tak prehodit do
                                                        #  prepare_data a sem to posilat jako argument 23.05.2018 MK
        mfda = False
        sr, itera = rainfall.load_precipitation(rainfall_file_path)

        return mat_efect_vrst, state_cell, mfda, sr, itera

    def save_raster(self, name, array_export, l_x, l_y, spix, vpix, NoDataValue, folder):
        ll_corner = arcpy.Point(l_x, l_y)
        raster = arcpy.NumPyArrayToRaster(
            array_export,
            ll_corner,
            spix,
            vpix,
            NoDataValue)
        raster.save(folder + os.sep + name)

    def find_boudary_cells(self, rows, cols, mat_nan, noData, mfda):
        # Identification of cells at the domain boundary

        mat_boundary = np.zeros([rows, cols], float)

        nr = range(rows)
        nc = range(cols)

        rcols = []
        rrows = []

        boundaryCols = []
        boundaryRows = []

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
                    boundaryRows.append(i)
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
            boundaryCols.append(oneColBoundary)

        return boundaryRows, boundaryCols, rrows, rcols, mat_boundary
