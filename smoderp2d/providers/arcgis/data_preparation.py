import shutil
import os
import sys
import numpy as np
import math
import csv

import smoderp2d.processes.rainfall as rainfall
from stream_preparation import StreamPreparation

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.base.exception import DataPreparationInvalidInput

# arcpy imports
from arcpy.sa import *
import arcpy
import arcgisscripting
from arcgis_dmtfce import dmtfce
import constants # poradi parametru z arcgis tool

class PrepareData(PrepareDataBase):

    def __init__(self):

        # creating the geoprocessor object
        self.gp = arcgisscripting.create()

        # setting the workspace environment
        self.gp.workspace = self.gp.GetParameterAsText(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

        # checking arcgis if ArcGIS Spatial extension is available
        arcpy.CheckOutExtension("Spatial")
        self.gp.overwriteoutput = 1

    def _get_input_params(self):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params['dmt'] = self.gp.GetParameterAsText(
            constants.PARAMETER_DMT)
        self._input_params['soil_indata'] = self.gp.GetParameterAsText(
            constants.PARAMETER_SOIL)
        self._input_params['stype'] = self.gp.GetParameterAsText(
            constants.PARAMETER_SOIL_TYPE)
        self._input_params['veg_indata'] = self.gp.GetParameterAsText(
            constants.PARAMETER_VEGETATION)
        self._input_params['vtype'] = self.gp.GetParameterAsText(
            constants.PARAMETER_VEGETATION_TYPE)
        self._input_params['rainfall_file_path'] = self.gp.GetParameterAsText(
            constants.PARAMETER_PATH_TO_RAINFALL_FILE)
        self._input_params['maxdt'] = float(self.gp.GetParameterAsText(
            constants.PARAMETER_MAX_DELTA_T))
        self._input_params['end_time'] = float(self.gp.GetParameterAsText(
            constants.PARAMETER_END_TIME)) * 60.0  # prevod na s
        self._input_params['points'] = self.gp.GetParameterAsText(
            constants.PARAMETER_POINTS)
        self._input_params['output'] = self.gp.GetParameterAsText(
            constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)
        self._input_params['tab_puda_veg'] = self.gp.GetParameterAsText(
            constants.PARAMETER_SOILVEGTABLE)
        self._input_params['tab_puda_veg_code'] = self.gp.GetParameterAsText(
            constants.PARAMETER_SOILVEGTABLE_CODE)
        self._input_params['stream'] = self.gp.GetParameterAsText(
            constants.PARAMETER_STREAM)
        self._input_params['tab_stream_tvar'] = self.gp.GetParameterAsText(
            constants.PARAMETER_STREAMTABLE)
        self._input_params['tab_stream_tvar_code'] = self.gp.GetParameterAsText(
            constants.PARAMETER_STREAMTABLE_CODE)

    def run(self):
        """Main function of data_preparation class. Returns computed
        parameters from input data using ArcGIS in a form of a
        dictionary.

        :return data: dictionary with model parameters.
        """
        super(PrepareData, self).run()


        self._add_message("Computing parameters of DMT...")
        # raster to numpy array conversion
        self.data['mat_dmt'] = self._rst2np(dmt_clip)
        self.data['mat_slope'] = self._rst2np(slope_clip)
        self.data['mat_fd'] = self._rst2np(flow_direction_clip)

        # TODO: add comments, describe
        ll_corner = self._get_raster_dim(dmt_clip)

        all_attrib = self._get_mat_par(sfield, intersect)

        self._get_array_points()

        self._get_a(all_attrib)

        self._get_crit_water(all_attrib, ll_corner)

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(rainfall_file_path)

        # compute aspect
        self._get_slope_dir(dmt_clip)

        self._add_message("\nSTREAM PREPARATION")
        self._prepare_streams(stream, tab_stream_tvar, tab_stream_tvar_code,
                              dmt, null_shp, ll_corner, dmt_clip, intersect)

        # determine cells on the boundary
        self._find_boundary_cells()

        self._save_raster("fl_dir", self.data['mat_fd'], self.data['temp'])

        self.data['mat_n'] = all_attrib[2]
        self.data['mat_ppl'] = all_attrib[3]
        self.data['mat_pi'] = all_attrib[4]
        self.data['mat_reten'] = all_attrib[5]
        self.data['mat_b'] = all_attrib[6]

        self.data['mfda'] = False
        self.data['mat_boundary'] = None
        self.data['points'] = None
        self.data['spix'] = None
        self.data['vpix'] = None

        self._add_message("\nData preparation has been finished\n")

        return self.data

    def _add_message(self, message):
        """
        Pops up a message into arcgis and saves it into log file.
        :param message: Message to be printed.
        """
        Logger.info(message)


    def _set_output(self):
        """Creates empty output and temporary directories to which created
        files are saved. Creates temporary ArcGIS File Geodatabase.

        """
        super(PrepareData, self)._set_output()

        # create temporary ArcGIS File Geodatabase
        arcpy.CreateFileGDB_management(
            self.data['temp'], "tempGDB.gdb"
        )

    def _set_mask(self):
        """TODO"""
        dmt_copy = os.path.join(
            self.data['temp'], "tempGDB.gdb", "dmt_copy")
        arcpy.CopyRaster_management(dmt, dmt_copy)

        # align computation region to DMT grid
        arcpy.env.snapRaster = dmt

        dmt_mask = os.path.join(self.data['temp'], "dmt_mask")
        self.gp.Reclassify_sa(
            dmt_copy, "VALUE", "-100000 100000 1", dmt_mask, "DATA"
        )  # reklasifikuje se vsechno na 1
        
        return dmt_copy, dmt_mask

    def _dmtfce(self, dmt):
        return dmtfce(dmt, self.data['temp'])
    
     def _get_intersect(self, dmt, mask,
                        veg_indata, soil_indata, vtype, stype,
                        tab_puda_veg, tab_puda_veg_code):
        """
        :param str dmt: DMT raster name
        :param str mask: raster mask name
        :param str veg_indata: vegetation input vector name
        :param soil_indata: soil input vector name
        :param vtype: attribute vegetation column for dissolve
        :param stype: attribute soil column for dissolve
        :param tab_puda_veg: soil table to join
        :param tab_puda_veg_code: key soil attribute 

        :return intersect: intersect vector name
        :return mask_shp: vector mask name
        :return sfield: list of selected attributes
        """
        # convert mask into polygon feature class
        mask_shp = os.path.join(self.data['temp'], "mask.shp")
        arcpy.RasterToPolygon_conversion(
            mask, mask_shp, "NO_SIMPLIFY")

        # dissolve soil and vegetation polygons
        soil_boundary = os.path.join(
            self.data['temp'], "s_b.shp")
        veg_boundary = os.path.join(
            self.data['temp'], "v_b.shp")
        arcpy.Dissolve_management(veg_indata, veg_boundary, vtype)
        arcpy.Dissolve_management(soil_indata, soil_boundary, stype)

        # do intersection
        group = [soil_boundary, veg_boundary, mask_shp]
        intersect = os.path.join(
            self.data['outdir'], "interSoilLU.shp")
        arcpy.Intersect_analysis(group, intersect, "ALL", "", "INPUT")

        # remove "puda_veg" if exists and create a new one
        if self.gp.ListFields(intersect, "puda_veg").Next():
            arcpy.DeleteField_management(intersect, "puda_veg")
        arcpy.AddField_management(
            intersect, "puda_veg", "TEXT", "", "", "15", "",
            "NULLABLE", "NON_REQUIRED","")

        # compute "puda_veg" values (stype + vtype)
        vtype1 = vtype + "_1" if stype == vtype else vtype
        fields = [stype, vtype1, "puda_veg"]
        with arcpy.da.UpdateCursor(intersect, fields) as cursor:
            for row in cursor:
                row[2] = row[0] + row[1]
                cursor.updateRow(row)

        # copy attribute table to DBF file for modifications
        puda_veg_dbf = os.path.join(
            self.data['temp'], "puda_veg_tab_current.dbf")
        arcpy.CopyRows_management(tab_puda_veg, puda_veg_dbf)

        # join table copy to intersect feature class
        sfield = ["k", "s", "n", "pi", "ppl",
                  "ret", "b", "x", "y", "tau", "v"]
        self._join_table(
            intersect, "puda_veg", puda_veg_dbf, tab_puda_veg_code,
            ";".join(sfield)
        )

        with arcpy.da.SearchCursor(intersect, sfield) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ": # TODO: empty string or NULL value?
                        raise DataPreparationInvalidInput(
                            "Values in soilveg tab are not correct"
                        )

        return intersect, mask_shp, sfield

    def _clip_data(self, dmt, intersect, slope, flow_direction):
        """
        Clip input data based on AOI.

        :param str dmt: raster DMT name
        :param str intersect: vector intersect feature call name
        :param str slope: raster slope name
        :param str flow_direction: raster flow direction name

        :return str dmt_clip: output clipped DMT name
        :return str slope_clip: output clipped slope name
        :return str flow_direction_clip: ouput clipped flow direction name

        """
        # TODO: check only None value
        # clip input vectors based on AOI
        if self.data['points'] and \
           (self.data['points'] != "#") and (self.data['points'] != ""):
            self.data['points'] = self._clip_points(intersect)

        # set extent from intersect vector map
        arcpy.env.extent = intersect

        # raster description
        dmt_desc = arcpy.Describe(dmt_copy)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # create raster mask based on interesect feature calll
        mask = os.path.join(self.data['temp'], "mask")
        arcpy.PolygonToRaster_conversion(
            intersect, "FID", mask, "MAXIMUM_AREA",
            cellsize = dmt_desc.MeanCellHeight)

        # cropping rasters
        dmt_clip = ExtractByMask(dmt_copy, mask)
        dmt_clip.save(os.path.join(self.data['outdir'], "dmt_clip"))
        slope_clip = ExtractByMask(slope_orig, mask)
        slope_clip.save(os.path.join(self.data['temp'], "slope_clip"))
        flow_direction_clip = ExtractByMask(flow_direction, mask)
        flow_direction_clip.save(os.path.join(self.data['outdir'], "flow_clip"))

        return dmt_clip, slope_clip, flow_direction_clip

    def _clip_points(self, intersect):
        """
        :param intersect: vector intersect feature class
        """
        # clip vector points based on intersect
        pointsClipCheck = os.path.join(
            self.data['outdir'], "pointsCheck.shp")
        arcpy.Clip_analysis(
            self.data['points'], intersect, pointsClipCheck
        )

        # count number of features (rows)
        npoints = arcpy.GetCount_management(self._input_params['points'])
        npoints_clipped = arcpy.GetCount_management(pointsClipCheck)
                
        diffpts = npoints - npoints_clipped
        if len(diffpts) > 0:
            Logger.warning(
                "{} points outside of computation domain will be ignored".format(len(diffpts))
            )

        self.data['points'] = pointsClipCheck

    def _get_attrib(self, sfield, intersect):
        """

        :param sfield:
        :param intersect:

        :return all_atrib:
        """

        mat_k = np.zeros([self.data['r'], self.data['c']], float)
        mat_s = np.zeros([self.data['r'], self.data['c']], float)
        mat_n = np.zeros([self.data['r'], self.data['c']], float)
        mat_ppl = np.zeros([self.data['r'], self.data['c']], float)
        mat_pi = np.zeros([self.data['r'], self.data['c']], float)
        mat_ret = np.zeros([self.data['r'], self.data['c']], float)
        mat_b = np.zeros([self.data['r'], self.data['c']], float)
        mat_x = np.zeros([self.data['r'], self.data['c']], float)
        mat_y = np.zeros([self.data['r'], self.data['c']], float)
        mat_tau = np.zeros([self.data['r'], self.data['c']], float)
        mat_v = np.zeros([self.data['r'], self.data['c']], float)

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
            all_attrib[poradi] = self._rst2np(d)
            poradi = poradi + 1
        return all_attrib

    def _rst2np(self,raster):
        """

        :param raster:

        :return:
        """
        return arcpy.RasterToNumPyArray(raster)

    def _get_raster_dim(self,dmt_clip):
        """

        :param dmt_clip:

        :return ll_corner:
        """

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

    def _get_mat_par(self, sfield, intersect):
        """

        :param sfield:
        :param intersect:

        :return all_atrib:
        """
        all_attrib = self._get_attrib(sfield, intersect)

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

        self._save_raster("mat_nan", self.data['mat_nan'], self.data['temp'])

        return all_attrib

    def _get_array_points(self):
        """

        """

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
            for row in rows_p:
                # getting points ID
                fid = row.getValue('FID')
                # create the geometry object 'feat'
                feat = row.getValue(shapefieldname)
                pnt = feat.getPart()

                # position i,j in raster
                r = self.data['r'] - ((pnt.Y - self.data['yllcorner']) // self.data['vpix']) - 1  # i from 0
                c = (pnt.X - self.data['xllcorner']) // self.data['spix']  # j

                # if point is not on the edge of raster or its neighbours are not "NoDataValue", it will be saved into
                # array_points array
                if r != 0 and r != self.data['r'] and c != 0 and c != self.data['c'] and \
                   self.data['mat_dmt'][r][c] != self.data['NoDataValue'] and \
                   self.data['mat_dmt'][r-1][c] != self.data['NoDataValue'] and \
                   self.data['mat_dmt'][r+1][c] != self.data['NoDataValue'] and \
                   self.data['mat_dmt'][r][c-1] != self.data['NoDataValue'] and \
                   self.data['mat_dmt'][r][c+1] != self.data['NoDataValue']:

                    self.data['array_points'][i][0] = fid
                    self.data['array_points'][i][1] = r
                    self.data['array_points'][i][2] = c
                    # x,y coordinates of current point stored in an array
                    self.data['array_points'][i][3] = pnt.X
                    self.data['array_points'][i][4] = pnt.Y
                    i = i + 1
                else:
                    self._add_message("Point FID = " + str(int(fid)) +
                                      " is at the edge of the raster. This point will not be included in results.")

        else:
            self.data['array_points'] = None



    def _get_a(self,all_attrib):
        """

        :param all_attrib:
        """

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

    def _get_crit_water(self, all_attrib, ll_corner):
        """

        :param all_attrib:
        :param ll_corner:
        """

        mat_b = all_attrib[6]
        mat_tau = all_attrib[9]
        mat_v = all_attrib[10]

        # critical water level
        self._add_message("Computing critical level")
        mat_hcrit_tau = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_v = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_flux = np.zeros([self.data['r'], self.data['c']], float)
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

    def _get_slope_dir(self,dmt_clip):
        """

        :param dmt_clip:
        """

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
        self.data['mat_efect_vrst'] = self._rst2np(efect_vrst)

    def _prepare_streams(self, stream, tab_stream_tvar, tab_stream_tvar_code, dmt, null_shp, ll_corner, dmt_clip, intersect):
        """

        :param stream:
        :param tab_stream_tvar:
        :param tab_stream_tvar_code:
        :param dmt:
        :param null_shp:
        :param ll_corner:
        :param dmt_clip:
        :param intersect:
        """
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

            input = [stream,
                     tab_stream_tvar,
                     tab_stream_tvar_code,
                     dmt,
                     null_shp,
                     self.data['spix'],
                     self.data['r'],
                     self.data['c'],
                     ll_corner,
                     self.data['outdir'],
                     dmt_clip,
                     intersect,
                     self._add_field,
                     self._join_table]

            self.data['toky'], self.data['mat_tok_reach'], self.data['toky_loc'] = StreamPreparation(input).prepare_streams()

        else:
            self.data['toky'] = None
            self.data['mat_tok_reach'] = None
            self.data['toky_loc'] = None

    def _add_field(self, input, newfield, datatype, default_value):  # EDL
        """
        Adds field into attribute field of feature class.

        :param input: Feature class to which new field is to be added.
        :param newfield:
        :param datatype:
        :param default_value:

        :return input: Feature class with new field.
        """

        try:
            arcpy.DeleteField_management(input, newfield)
        except:
            pass
        arcpy.AddField_management(input, newfield, datatype)
        arcpy.CalculateField_management(input, newfield, default_value, "PYTHON")
        return input

    def _join_table(self, in_data, in_field, join_table, join_field, fields=None):
        """

        :param in_data:
        :param in_field:
        :param join_table:
        :param join_field:
        :param fields:
        :return:
        """
        if fields == None:
            arcpy.JoinField_management(
                in_data, in_field, join_table, join_field)
        else:
            arcpy.JoinField_management(
                in_data, in_field, join_table, join_field, fields)

    def _save_raster(self, name, array_export, folder):
        """

        :param name:
        :param array_export:
        :param folder:
        """

        raster = arcpy.NumPyArrayToRaster(array_export,
                                          arcpy.Point(self.data['xllcorner'], self.data['yllcorner']),
                                          self.data['spix'],
                                          self.data['vpix'],
                                          self.data['NoDataValue'])
        raster.save(folder + os.sep + name)

    def _find_boundary_cells(self):
        """

        """
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
