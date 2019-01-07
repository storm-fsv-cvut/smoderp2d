import shutil
import os
import sys
import numpy as np
import math
import csv

import smoderp2d.processes.rainfall as rainfall

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.base.exception import DataPreparationInvalidInput

from smoderp2d.providers.arcgis.stream_preparation import StreamPreparation
from smoderp2d.providers.arcgis.dmtfce import dmtfce
import smoderp2d.providers.arcgis.constants as constants

from arcpy.sa import *
import arcpy
import arcgisscripting

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

        self._save_raster("fl_dir", self.data['mat_fd'], self.data['temp'])

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
        arcpy.CopyRaster_management(self._input_params['dmt'], dmt_copy)

        # align computation region to DMT grid
        arcpy.env.snapRaster = self._input_params['dmt']

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
        dmt_desc = arcpy.Describe(dmt)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dmt_desc.SpatialReference

        # create raster mask based on interesect feature calll
        mask = os.path.join(self.data['temp'], "mask")
        arcpy.PolygonToRaster_conversion(
            intersect, "FID", mask, "MAXIMUM_AREA",
            cellsize = dmt_desc.MeanCellHeight)

        # cropping rasters
        dmt_clip = ExtractByMask(dmt, mask)
        dmt_clip.save(os.path.join(self.data['outdir'], "dmt_clip"))
        slope_clip = ExtractByMask(slope, mask)
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
                
        diffpts = int(npoints[0]) - int(npoints_clipped[0])
        if diffpts > 0:
            Logger.warning(
                "{} points outside of computation domain will be ignored".format(diffpts)
            )

        self.data['points'] = pointsClipCheck

    def _get_attrib(self, sfield, intersect):
        """
        Get numpy arrays of selected attributes.

        :param sfield: list of attributes
        :param intersect: vector intersect name

        :return all_atrib: list of numpy array
        """
        dim = [self.data['r'], self.data['c']]
        
        mat_k = np.zeros(dim, float)
        mat_s = np.zeros(dim, float)
        mat_n = np.zeros(dim, float)
        mat_ppl = np.zeros(dim, float)
        mat_pi = np.zeros(dim, float)
        mat_ret = np.zeros(dim, float)
        mat_b = np.zeros(dim, float)
        mat_x = np.zeros(dim, float)
        mat_y = np.zeros(dim, float)
        mat_tau = np.zeros(dim, float)
        mat_v = np.zeros(dim, float)

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
            mat_v
        ] 

        idx = 0
        for field in sfield:
            output = os.path.join(self.data['temp'], "r{}".format(field))
            arcpy.PolygonToRaster_conversion(
                intersect, field, output,
                "MAXIMUM_AREA", "", self.data['vpix']
            )
            all_attrib[idx] = self._rst2np(output)
            idx += 1
            
        return all_attrib

    def _rst2np(self, raster):
        """
        Convert raster data into numpy array

        :param raster: raster name

        :return: numpy array
        """
        return arcpy.RasterToNumPyArray(raster)

    def _get_raster_dim(self, dmt_clip):
        """
        Get raster spatial reference info.

        :param dmt_clip: clipped dmt raster map
        """
        dmt_desc = arcpy.Describe(dmt_clip)
        
        # lower left corner coordinates
        self.data['xllcorner'] = dmt_desc.Extent.XMin
        self.data['yllcorner'] = dmt_desc.Extent.YMin
        self.data['NoDataValue'] = dmt_desc.noDataValue
        self.data['vpix'] = dmt_desc.MeanCellHeight
        self.data['spix'] = dmt_desc.MeanCellWidth
        self.data['pixel_area'] = self.data['spix'] * self.data['vpix']

        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dmt'].shape[0]
        self.data['c'] = self.data['mat_dmt'].shape[1]

    def _get_array_points(self):
        """Get array of points. Points near AOI border are skipped.

        """
        # getting points coordinates from optional input shapefile
        if self.data['points'] and \
           (self.data['points'] != "#") and (self.data['points'] != ""):
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
                if r != 0 and r != self.data['r'] \
                   and c != 0 and c != self.data['c'] and \
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
                    i += 1
                else:
                    Logger.info(
                        "Point FID = {} is at the edge of the raster." 
                        "This point will not be included in results.".format(
                            fid
                    ))
        else:
            self.data['array_points'] = None

    def _get_slope_dir(self, dmt_clip):
        """
        ?

        :param dmt_clip:
        """

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok
        # ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dmt_clip)
        asppii = arcpy.sa.Times(asp, pii)
        sinasp = arcpy.sa.Sin(asppii)
        cosasp = arcpy.sa.Cos(asppii)
        sinsklon = arcpy.sa.Abs(sinasp)
        cossklon = arcpy.sa.Abs(cosasp)
        times1 = arcpy.sa.Plus(cossklon, sinsklon)
        times1.save(os.path.join(self.data['temp'], "ratio_cell"))

        efect_vrst = arcpy.sa.Times(times1, self.data['spix'])
        efect_vrst.save(os.path.join(self.data['temp'], "efect_vrst"))
        self.data['mat_efect_vrst'] = self._rst2np(efect_vrst)

    def _prepare_streams(self, mask_shp, dmt_clip, intersect):
        """

        :param mask_shp:
        :param dmt_clip:
        :param intersect:
        """
        self.data['type_of_computing'] = 1

        ll_corner = arcpy.Point(
            self.data['xllcorner'], self.data['yllcorner']
        )

        # pocitam vzdy s ryhama pokud jsou zadane vsechny vstupy pro
        # vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [self._input_params['stream'],
                  self._input_params['tab_stream_tvar'],
                  self._input_params['tab_stream_tvar_code']]
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            self.data['type_of_computing'] = 3

        if self.data['type_of_computing'] == 3 or \
           self.data['type_of_computing'] == 5:

            input = [self._input_params['stream'],
                     self._input_params['tab_stream_tvar'],
                     self._input_params['tab_stream_tvar_code'],
                     self._input_params['dmt'],
                     mask_shp,
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

    def _save_raster(self, name, array_export, folder=None):
        """
        Convert numpy array into raster file.

        :param name: raster file
        :param array_export: data array
        :param folder: target folder (if not specified use temporary directory)
        """
        if not folder:
            folder = self.data['temp']
        raster = arcpy.NumPyArrayToRaster(
            array_export,
            arcpy.Point(self.data['xllcorner'], self.data['yllcorner']),
            self.data['spix'],
            self.data['vpix'],
            self.data['NoDataValue'])
        raster.save(os.path.join(folder, name))

