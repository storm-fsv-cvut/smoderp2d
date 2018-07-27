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
        Logger.info(message)

    def run(self):
    # main function of data_preparation class

        self.create_dict()

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

        self.data['maxdt'] = maxdt
        self.data['end_time'] = end_time
        self.data['outdir'] = output
        self.data['points'] = points

        # deleting output directory
        shutil.rmtree(self.data['outdir'])

        if not os.path.exists(self.data['outdir']):
            os.makedirs(self.data['outdir'])
        self.add_message("Creating of the output directory: " + self.data['outdir'])

        self.data['temp'] = self.data['outdir'] + os.sep + "temp"

        if not os.path.exists(self.data['temp']):
            os.makedirs(self.data['temp'])

        self.add_message("Creating of the temp: " + self.data['temp'])

        arcpy.env.snapRaster = dmt
        # deleting content of output directory
        dirList = os.listdir(self.data['outdir'])  # arcgis bug - locking shapefiles
        ab = 0
        for fname in dirList:
            if "sr.lock" in fname:
                ab = 1

        if ab == 0:
            contents = [os.path.join(self.data['outdir'], i) for i in os.listdir(self.data['outdir'])]

            [shutil.rmtree(i) if os.path.isdir(i) else os.unlink(i)
             for i in contents]

        if not os.path.exists(self.data['temp']):
            os.makedirs(self.data['temp'])

        temp_gdb = arcpy.CreateFileGDB_management (self.data['temp'], "tempGDB.gdb")
        dmt_copy = self.data['temp'] + os.sep + "tempGDB.gdb" + os.sep + "dmt_copy"

        arcpy.CopyRaster_management(dmt, dmt_copy)

        Logger.info("DMT preparation...")

        dmt_fill, flow_direction, flow_accumulation, slope_orig = arcgis_dmtfce.dmtfce(dmt_copy, self.data['temp'],
                                                                                       "TRUE", "TRUE", "NONE")

        # intersect
        intersect, null_shp, sfield = self.get_intersect(dmt_copy, veg_indata, soil_indata, vtyp, ptyp, gp,
                                                         tab_puda_veg, tab_puda_veg_code)

        # clip
        flow_direction_clip, slope_clip, dmt_clip = self.clip_data(dmt_copy, intersect, slope_orig, flow_direction)

        # self.save_raster("fl_dir", mat_fd, x_coordinate, y_coordinate, spix, vpix, NoDataValue, self.temp)

        # raster to numpy array conversion
        self.data['mat_dmt']    = self.rst2np(dmt_clip)
        self.data['mat_slope']  = self.rst2np(slope_clip)
        self.data['mat_fd']     = self.rst2np(flow_direction_clip)

        ll_corner = self.get_raster_dim(dmt_clip)

        all_attrib = self.get_mat_par(sfield, intersect)

        self.get_array_points(gp)

        self.get_a(all_attrib)

        self.crit_water( all_attrib, ll_corner)

        self.data['sr'], self.data['itera'] = rainfall.load_precipitation(rainfall_file_path)

        self.slope_dir(dmt_clip)

        self.stream_prep(stream, tab_stream_tvar, tab_stream_tvar_code, dmt, null_shp, ll_corner, dmt_clip, intersect)

        self.find_boundary_cells()

        self.data['mat_n']     = all_attrib[2]
        self.data['mat_ppl']   = all_attrib[3]
        self.data['mat_pi']    = all_attrib[4]
        self.data['mat_reten'] = all_attrib[5]
        self.data['mat_b']     = all_attrib[6]

        self.data['mfda']    = False
        self.data['mat_boundary'] = None
        self.data['points'] = None
        self.data['spix']   = None
        self.data['vpix']   = None

        self.add_message("Data preparation has been finished")

        return self.data

    def create_dict(self):
        self.data = {
            'br': None,
            'bc': None,
            'mat_boundary': None,
            'rr': None,
            'rc': None,
            'outletCells': None,
            'xllcorner': None,
            'yllcorner': None,
            'NoDataValue': None,
            'array_points': None,
            'c': None,
            'r': None,
            'combinatIndex': None,
            'maxdt': None,
            'mat_pi': None,
            'mat_ppl': None,
            'surface_retention': None,
            'mat_inf_index': None,
            'mat_hcrit': None,
            'mat_aa': None,
            'mat_b': None,
            'mat_reten': None,
            'mat_fd': None,
            'mat_dmt': None,
            'mat_efect_vrst': None,
            'mat_slope': None,
            'mat_nan': None,
            'mat_a': None,
            'mat_n': None,
            'outdir': None,
            'pixel_area': None,
            'points': None,
            'poradi': None,
            'end_time': None,
            'spix': None,
            'state_cell': None,
            'temp': None,
            'type_of_computing': None,
            'vpix': None,
            'mfda': None,
            'sr': None,
            'itera': None,
            'toky': None,
            'cell_stream': None,
            'mat_tok_reach': None,
            'STREAM_RATIO': None,
            'toky_loc': None
            }

    def add_field(self, input, newfield, datatype, default_value):  # EDL
        # function for adding fields
        try:
            arcpy.DeleteField_management(input, newfield)
        except:
            pass
        arcpy.AddField_management(input, newfield, datatype)
        arcpy.CalculateField_management(input, newfield, default_value, "PYTHON")
        return input

    def get_intersect(self, dmt_copy, veg_indata, soil_indata, vtyp, ptyp, gp, tab_puda_veg, tab_puda_veg_code):
        # adding attribute for soil and vegetation into attribute table (type short int)
        # preparation for clip
        null = self.data['temp'] + os.sep + "hrance_rst"
        null_shp = self.data['temp'] + os.sep + "null.shp"
        arcpy.gp.Reclassify_sa(dmt_copy, "VALUE", "-100000 100000 1", null, "DATA")  # reklasifikuje se vsechno na 1
        arcpy.RasterToPolygon_conversion(null, null_shp, "NO_SIMPLIFY")

        soil_boundary = self.data['temp'] + os.sep + "s_b.shp"
        veg_boundary = self.data['temp'] + os.sep + "v_b.shp"

        arcpy.Dissolve_management(veg_indata, veg_boundary, vtyp)
        arcpy.Dissolve_management(soil_indata, soil_boundary, ptyp)

        group = [soil_boundary, veg_boundary, null_shp]
        intersect = self.data['outdir'] + os.sep + "interSoilLU.shp"
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

        puda_veg_dbf = self.data['temp'] + os.sep + "puda_veg_tab_current.dbf"

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


    def clip_data(self, dmt_copy, intersect, slope_orig, flow_direction):

        # mask and clip data
        self.add_message("Clip of the source data by intersect")

        if self.data['points'] and (self.data['points'] != "#") and (self.data['points'] != ""):
            self.data['points'] = self.clip_points(intersect)

        arcpy.env.extent = intersect

        # raster description
        dmt_desc = arcpy.Describe(dmt_copy)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # size of cell
        self.data['vpix'] = dmt_desc.MeanCellHeight

        maska = self.data['temp'] + os.sep + "maska"
        arcpy.PolygonToRaster_conversion(intersect, "FID", maska, "MAXIMUM_AREA", cellsize=self.data['vpix'])

        # cropping rasters
        dmt_clip = ExtractByMask(dmt_copy, maska)
        dmt_clip.save(self.data['outdir'] + os.sep + "DMT")
        slope_clip = ExtractByMask(slope_orig, maska)
        slope_clip.save(self.data['temp'] + os.sep + "slope_clip")

        flow_direction_clip = ExtractByMask(flow_direction, maska)
        flow_direction_clip.save(self.data['outdir'] + os.sep + "flowDir")

        return flow_direction_clip, slope_clip, dmt_clip

    def clip_points(self, intersect):
        tmpPoints = []
        desc = arcpy.Describe(self.data['points'])
        shapefieldname = desc.ShapeFieldName
        rows_p = arcpy.SearchCursor(self.data['points'])
        for row in rows_p:
            feat = row.getValue(shapefieldname)
            pnt = feat.getPart()
            tmpPoints.append([pnt.X, pnt.Y])
        del rows_p

        pointsClipCheck = self.data['outdir'] + os.sep + "pointsCheck.shp"
        arcpy.Clip_analysis(self.data['points'], intersect, pointsClipCheck)

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

        self.data['points'] = pointsClipCheck

    def get_attrib(self, sfield, intersect):

        mat_k   = np.zeros([self.data['r'], self.data['c']], float)
        mat_s   = np.zeros([self.data['r'], self.data['c']], float)
        mat_n   = np.zeros([self.data['r'], self.data['c']], float)
        mat_ppl = np.zeros([self.data['r'], self.data['c']], float)
        mat_pi  = np.zeros([self.data['r'], self.data['c']], float)
        mat_ret = np.zeros([self.data['r'], self.data['c']], float)
        mat_b   = np.zeros([self.data['r'], self.data['c']], float)
        mat_x   = np.zeros([self.data['r'], self.data['c']], float)
        mat_y   = np.zeros([self.data['r'], self.data['c']], float)
        mat_tau = np.zeros([self.data['r'], self.data['c']], float)
        mat_v   = np.zeros([self.data['r'], self.data['c']], float)

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
            d = self.data['temp'] + os.sep + "r" + str(x)
            arcpy.PolygonToRaster_conversion(intersect, str(x), d, "MAXIMUM_AREA", "", self.data['vpix'])
            all_attrib[poradi] = self.rst2np(d)
            poradi = poradi + 1
        return all_attrib

    def rst2np(self,raster):
        return arcpy.RasterToNumPyArray(raster)

    def get_raster_dim(self,dmt_clip):

        # cropped raster info
        dmt_desc = arcpy.Describe(dmt_clip)
        # lower left corner coordinates
        self.data['xllcorner'] = dmt_desc.Extent.XMin
        self.data['yllcorner'] = dmt_desc.Extent.YMin
        self.data['NoDataValue'] = dmt_desc.noDataValue
        self.data['vpix'] = dmt_desc.MeanCellHeight
        self.data['spix'] = dmt_desc.MeanCellWidth
        self.data['pixel_area'] = self.data['spix'] * self.data['vpix']
        ll_corner = arcpy.Point(self.data['xllcorner'], self.data['yllcorner'])

        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dmt'].shape[0]
        self.data['c'] = self.data['mat_dmt'].shape[1]

        return ll_corner

    def get_mat_par(self, sfield, intersect):

        all_attrib = self.get_attrib(sfield, intersect)

        self.data['mat_nan'] = np.zeros([self.data['r'], self.data['c']], float)
        mat_k = all_attrib[0]
        mat_s = all_attrib[1]
        self.data['mat_inf_index'] = None
        self.data['combinatIndex'] = None

        infiltration_type = int(0)  # "Phillip"
        if infiltration_type == int(0):  #to se rovna vzdycky ne? nechapu tuhle podminku 23.05.2018 MK
            self.data['mat_inf_index'] = np.zeros([self.data['r'], self.data['c']], int)
            combinat = []
            self.data['combinatIndex'] = []
            for i in range(self.data['r']):
                for j in range(self.data['c']):
                    kkk = mat_k[i][j]
                    sss = mat_s[i][j]
                    ccc = [kkk, sss]
                    try:
                        if combinat.index(ccc):
                            self.data['mat_inf_index'][i][j] = combinat.index(ccc)
                    except:
                        combinat.append(ccc)
                        self.data['combinatIndex'].append([combinat.index(ccc), kkk, sss, 0])
                        self.data['mat_inf_index'][i][j] = combinat.index(ccc)

        # vyrezani krajnich bunek, kde byly chyby, je to vyrazeno u sklonu a acc
        i = 0
        j = 0

        # data value vector intersection
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                x_mat_dmt = self.data['mat_dmt'][i][j]
                slp = self.data['mat_slope'][i][j]
                if x_mat_dmt == self.data['NoDataValue'] or slp == self.data['NoDataValue']:
                    self.data['mat_nan'][i][j] = self.data['NoDataValue']
                    self.data['mat_slope'][i][j] = self.data['NoDataValue']
                    self.data['mat_dmt'][i][j] = self.data['NoDataValue']
                else:
                    self.data['mat_nan'][i][j] = 0

        return all_attrib

    def get_array_points(self, gp):
        # getting points coordinates from optional input shapefile
        if self.data['points'] and (self.data['points'] != "#") and (self.data['points'] != ""):
            # identify the geometry field
            desc = arcpy.Describe(self.data['points'])
            shapefieldname = desc.ShapeFieldName
            # create search cursor
            rows_p = arcpy.SearchCursor(self.data['points'])
            # getting number of points in shapefile
            count = arcpy.GetCount_management(self.data['points'])  # result
            count = count.getOutput(0)

            # empty array
            self.data['array_points'] = np.zeros([int(count), 5], float)

            i = 0
            # each point is saved into matrix from second row to the end. First row
            # is for maximal value from flow accumulation array
            for row in rows_p:
                # getting points ID
                fid = row.getValue('FID')
                self.data['array_points'][i][0] = fid
                # create the geometry object 'feat'
                feat = row.getValue(shapefieldname)
                pnt = feat.getPart()
                # position i,j in raster
                self.data['array_points'][i][1] = self.data['r'] - ((pnt.Y - self.data['yllcorner']) // self.data['vpix']) - 1  # i
                self.data['array_points'][i][2] = (pnt.X - self.data['xllcorner']) // self.data['spix']  # j
                # x,y coordinates of current point stored in an array
                self.data['array_points'][i][3] = pnt.X
                self.data['array_points'][i][4] = pnt.Y
                i = i + 1

        else:
            self.data['array_points'] = None

        # checking for points at the edge of the raster
        if self.data['points'] and self.data['points'] != "#":
            for kyk in range(self.data['array_points'].shape[0] - 1):
                if self.data['array_points'][kyk][1] == i and self.data['array_points'][kyk][2] == j:
                    gp.AddMessage("Point FID = " + str(
                        int(self.data['array_points'][kyk][
                                0])) + " is at the edge of the raster. This point will not be included in results.")
                    self.data['array_points'] = np.delete(self.data['array_points'], kyk, 0)

    def get_a(self,all_attrib):
        mat_n = all_attrib[2]
        mat_x = all_attrib[7]
        mat_y = all_attrib[8]
        self.data['mat_a']  = np.zeros([self.data['r'], self.data['c']], float)
        self.data['mat_aa'] = np.zeros([self.data['r'], self.data['c']], float)

        # calculating the "a" parameter
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                slope = self.data['mat_slope'][i][j]
                par_x = mat_x[i][j]
                par_y = mat_y[i][j]

                if par_x == self.data['NoDataValue'] or par_y == self.data['NoDataValue'] or slope == self.data['NoDataValue']:
                    par_a = self.data['NoDataValue']
                    par_aa = self.data['NoDataValue']

                elif par_x == self.data['NoDataValue'] or par_y == self.data['NoDataValue'] or slope == 0.0:
                    par_a = 0.0001
                    par_aa = par_a / 100 / mat_n[i][j]

                else:
                    exp = np.power(slope, par_y)
                    par_a = par_x * exp
                    par_aa = par_a / 100 / mat_n[i][j]

                self.data['mat_a'][i][j] = par_a
                self.data['mat_aa'][i][j] = par_aa

    def crit_water(self, all_attrib, ll_corner):

        mat_b = all_attrib[6]
        mat_tau = all_attrib[9]
        mat_v = all_attrib[10]

        # critical water level
        self.add_message("Computing critical level")
        mat_hcrit_tau   = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_v     = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_flux  = np.zeros([self.data['r'], self.data['c']], float)
        self.data['mat_hcrit'] = np.zeros([self.data['r'], self.data['c']], float)
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                if self.data['mat_slope'][i][j] != self.data['NoDataValue'] and mat_tau[i][j] != self.data['NoDataValue']:
                    slope = self.data['mat_slope'][i][j]
                    tau_crit = mat_tau[i][j]
                    v_crit = mat_v[i][j]
                    b = mat_b[i][j]
                    aa = self.data['mat_aa'][i][j]
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
                    self.data['mat_hcrit'][i][j] = hcrit
                else:
                    mat_hcrit_tau[i][j] = self.data['NoDataValue']
                    mat_hcrit_v[i][j] = self.data['NoDataValue']
                    mat_hcrit_flux[i][j] = self.data['NoDataValue']
                    self.data['mat_hcrit'][i][j] = self.data['NoDataValue']

        rhcrit_tau = arcpy.NumPyArrayToRaster(mat_hcrit_tau, ll_corner, self.data['spix'], self.data['vpix'], "#")
        rhcrit_tau.save(self.data['temp'] + os.sep + "hcrit_tau")

        rhcrit_flux = arcpy.NumPyArrayToRaster(mat_hcrit_flux, ll_corner, self.data['spix'], self.data['vpix'], "#")
        rhcrit_flux.save(self.data['temp'] + os.sep + "hcrit_flux")

        rhcrit_v = arcpy.NumPyArrayToRaster(mat_hcrit_v, ll_corner, self.data['spix'], self.data['vpix'], "#")
        rhcrit_v.save(self.data['temp'] + os.sep + "hcrit_v")

    def slope_dir(self,dmt_clip):

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dmt_clip)
        asppii = arcpy.sa.Times(asp, pii)
        sinasp = arcpy.sa.Sin(asppii)
        cosasp = arcpy.sa.Cos(asppii)
        sinsklon = arcpy.sa.Abs(sinasp)
        cossklon = arcpy.sa.Abs(cosasp)
        times1 = arcpy.sa.Plus(cossklon, sinsklon)
        times1.save(self.data['temp'] + os.sep + "ratio_cell")

        efect_vrst = arcpy.sa.Times(times1, self.data['spix'])
        efect_vrst.save(self.data['temp'] + os.sep + "efect_vrst")
        self.data['mat_efect_vrst'] = self.rst2np(efect_vrst)

    def stream_prep(self, stream, tab_stream_tvar, tab_stream_tvar_code, dmt, null_shp, ll_corner, dmt_clip, intersect):

        self.data['type_of_computing'] = 1

        # pocitam vzdy s ryhama
        # pokud jsou zadane vsechny vstupy pro vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [stream, tab_stream_tvar, tab_stream_tvar_code]
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            self.data['type_of_computing'] = 3
        else:
            pass

        if (self.data['type_of_computing'] == 3) or (self.data['type_of_computing'] == 5):

            self.add_message("Stream preparation...")

            self.data['toky'], self.data['mat_tok_reach'], self.data['toky_loc'] = sp.prepare_streams(listin, dmt, null_shp, self.data['mat_nan'], self.data['spix'],
                                                             self.data['r'], self.data['c'], ll_corner, self.add_field,
                                                             self.data['outdir'], dmt_clip, intersect)

            self.add_message("Stream preparation has finished")

        else:
            self.data['toky'] = None
            self.data['mat_tok_reach'] = None
            self.data['toky_loc'] = None

    def save_raster(self, name, array_export, l_x, l_y, folder):
        ll_corner = arcpy.Point(l_x, l_y)
        raster = arcpy.NumPyArrayToRaster(
            array_export,
            ll_corner,
            self.data['spix'],
            self.data['vpix'],
            self.data['NoDataValue'])
        raster.save(folder + os.sep + name)

    def find_boundary_cells(self):
        # Identification of cells at the domain boundary

        self.data['mat_boundary'] = np.zeros([self.data['r'], self.data['c']], float)

        nr = range(self.data['r'])
        nc = range(self.data['c'])

        self.data['rc'] = []
        self.data['rr'] = []

        for i in nr:
            for j in nc:
                val = self.data['mat_nan'][i][j]
                if i == 0 or j == 0 or i == (self.data['r'] - 1) or j == (self.data['c'] - 1):
                    if val != self.data['NoDataValue']:
                        val = -99
                else:
                    if val != self.data['NoDataValue']:
                        if  self.data['mat_nan'][i - 1][j] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i][j - 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i][j - 1] == self.data['NoDataValue']:

                            val = -99

                        if  self.data['mat_nan'][i - 1][j + 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j + 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i - 1][j - 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j - 1] == self.data['NoDataValue']:

                            val = -99.

                self.data['mat_boundary'][i][j] = val

        inDomain = False
        inBoundary = False

        for i in nr:
            oneCol = []
            oneColBoundary = []
            for j in nc:

                if self.data['mat_boundary'][i][j] == -99 and inBoundary == False:
                    inBoundary = True

                if self.data['mat_boundary'][i][j] == -99 and inBoundary:
                    oneColBoundary.append(j)

                if (self.data['mat_boundary'][i][j] == 0.0) and inDomain == False:
                    self.data['rr'].append(i)
                    inDomain = True

                if (self.data['mat_boundary'][i][j] == 0.0) and inDomain:
                    oneCol.append(j)

            inDomain = False
            inBoundary = False
            self.data['rc'].append(oneCol)