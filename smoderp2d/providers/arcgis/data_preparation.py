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
from smoderp2d.providers.arcgis.terrain import compute_products
import smoderp2d.providers.arcgis.constants as constants

from arcpy.sa import *
import arcpy
import arcgisscripting

class PrepareData(PrepareDataBase):
    def __init__(self):
        super(PrepareData, self).__init__()

        # creating the geoprocessor object
        self.gp = arcgisscripting.create()

        # setting the workspace environment
        self.gp.workspace = self.gp.GetParameterAsText(
            constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY
        )

        # checking arcgis if ArcGIS Spatial extension is available
        arcpy.CheckOutExtension("Spatial")
        self.gp.overwriteoutput = 1

        # get input parameters
        self._get_input_params()

    def _get_input_params(self):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params = {
            'elevation': self.gp.GetParameterAsText(
                constants.PARAMETER_DEM),
            'soil': self.gp.GetParameterAsText(
                constants.PARAMETER_SOIL),
            'soil_type': self.gp.GetParameterAsText(
                constants.PARAMETER_SOIL_TYPE),
            'vegetation': self.gp.GetParameterAsText(
                constants.PARAMETER_VEGETATION),
            'vegetation_type': self.gp.GetParameterAsText(
                constants.PARAMETER_VEGETATION_TYPE),
            'rainfall_file': self.gp.GetParameterAsText(
                constants.PARAMETER_PATH_TO_RAINFALL_FILE),
            'maxdt': float(self.gp.GetParameterAsText(
                constants.PARAMETER_MAX_DELTA_T)),
            'end_time': float(self.gp.GetParameterAsText(
                constants.PARAMETER_END_TIME)) * 60.0,  # prevod na s
            'points': self.gp.GetParameterAsText(
                constants.PARAMETER_POINTS),
            'output': self.gp.GetParameterAsText(
                constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY),
            'table_soil_vegetation': self.gp.GetParameterAsText(
                constants.PARAMETER_SOILVEGTABLE),
            'table_soil_vegetation_code': self.gp.GetParameterAsText(
                constants.PARAMETER_SOILVEGTABLE_CODE),
            'stream': self.gp.GetParameterAsText(
                constants.PARAMETER_STREAM),
            'table_stream_shape': self.gp.GetParameterAsText(
                constants.PARAMETER_STREAMTABLE),
            'table_stream_shape_code': self.gp.GetParameterAsText(
                constants.PARAMETER_STREAMTABLE_CODE)
        }

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
        self._tempGDB = os.path.join(self.data['temp'], "tempGDB.gdb")
        arcpy.CreateFileGDB_management(
            self.data['temp'], "tempGDB.gdb"
        )

    def _set_mask(self):
        """Set mask from elevation map.

        :return: dem copy, mask
        """
        dem_copy = os.path.join(self._tempGDB, "dem_copy")
        arcpy.CopyRaster_management(
            self._input_params['elevation'], dem_copy
        )

        # align computation region to DTM grid
        arcpy.env.snapRaster = self._input_params['elevation']

        dem_mask = os.path.join(self.data['temp'], "dem_mask")
        self.gp.Reclassify_sa(
            dem_copy, "VALUE", "-100000 100000 1", dem_mask, "DATA"
        )
        
        return dem_copy, dem_mask

    def _terrain_products(self, dem):
        """Computes terrains products.

        :param str elev: DTM raster map name
        
        :return: (filled elevation, flow direction, flow accumulation, slope)
        """
        return compute_products(dem, self.data['temp'])
    
    def _get_intersect(self, dem, mask,
                        vegetation, soil, vegetation_type, soil_type,
                        table_soil_vegetation, table_soil_vegetation_code):
        """
        Intersect data by area of interest.


        :param str dem: DTM raster name
        :param str mask: raster mask name
        :param str vegetation: vegetation input vector name
        :param soil: soil input vector name
        :param vegetation_type: attribute vegetation column for dissolve
        :param soil_type: attribute soil column for dissolve
        :param table_soil_vegetation: soil table to join
        :param table_soil_vegetation_code: key soil attribute 

        :return intersect: intersect vector name
        :return mask_shp: vector mask name
        :return sfield: list of selected attributes
        """
        # convert mask into polygon feature class
        mask_shp = os.path.join(
            self.data['temp'], "{}.shp".format(
                self._data['vector_mask']
        ))
        arcpy.RasterToPolygon_conversion(
            mask, mask_shp, "NO_SIMPLIFY")

        # dissolve soil and vegmetation polygons
        soil_boundary = os.path.join(
            self.data['temp'], "{}.shp".format(
                self._data['soil_boundary']
        ))
        vegetation_boundary = os.path.join(
            self.data['temp'], "{}.shp".format(
                self._data['vegetation_boundary']
        ))
        arcpy.Dissolve_management(
            vegetation, vegetation_boundary, vegetation_type
        )
        arcpy.Dissolve_management(
            soil, soil_boundary, soil_type
        )

        # do intersection
        group = [soil_boundary, vegetation_boundary, mask_shp]
        intersect = os.path.join(
            self.data['outdir'], "{}.shp".format(
                self._data['intersect']
        ))
        arcpy.Intersect_analysis(
            group, intersect, "ALL", "", "INPUT")

        # remove "soil_veg" if exists and create a new one
        if self.gp.ListFields(intersect, self._data['soil_veg_column']).Next():
            arcpy.DeleteField_management(intersect, self._data['soil_veg_column'])
        arcpy.AddField_management(
            intersect, self._data['soil_veg_column'], "TEXT", "", "", "15", "",
            "NULLABLE", "NON_REQUIRED","")

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        fields = [soil_type, vtype1, self._data['soil_veg_column']]
        with arcpy.da.UpdateCursor(intersect, fields) as cursor:
            for row in cursor:
                row[2] = row[0] + row[1]
                cursor.updateRow(row)

        # copy attribute table to DBF file for modifications
        soil_veg_copy = os.path.join(
            self.data['temp'], "{}.dbf".format(
                self._data['soil_veg_copy']
        ))
        arcpy.CopyRows_management(table_soil_vegetation, soil_veg_copy)

        # join table copy to intersect feature class
        self._join_table(
            intersect, self._data['soil_veg_column'],
            soil_veg_copy,
            table_soil_vegetation_code,
            ";".join(self._data['sfield'])
        )

        # check for empty values
        with arcpy.da.SearchCursor(intersect, self._data['sfield']) as cursor:
            for row in cursor:
                for i in range(len(row)):
                    if row[i] == " ": # TODO: empty string or NULL value?
                        raise DataPreparationInvalidInput(
                            "Values in soilveg tab are not correct"
                        )

        return intersect, mask_shp, self._data['sfield']

    def _clip_data(self, dem, intersect, slope, flow_direction):
        """
        Clip input data based on AOI.

        :param str dem: raster DTM name
        :param str intersect: vector intersect feature call name
        :param str slope: raster slope name
        :param str flow_direction: raster flow direction name

        :return str dem_clip: output clipped DTM name
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
        dem_desc = arcpy.Describe(dem)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dem_desc.SpatialReference

        # create raster mask based on interesect feature calll
        mask = os.path.join(self.data['temp'], "mask")
        arcpy.PolygonToRaster_conversion(
            intersect, "FID", mask, "MAXIMUM_AREA",
            cellsize = dem_desc.MeanCellHeight)

        # cropping rasters
        dem_clip = ExtractByMask(dem, mask)
        dem_clip.save(os.path.join(self.data['outdir'], "dem_clip"))
        slope_clip = ExtractByMask(slope, mask)
        slope_clip.save(os.path.join(self.data['temp'], "slope_clip"))
        flow_direction_clip = ExtractByMask(flow_direction, mask)
        flow_direction_clip.save(os.path.join(self.data['outdir'], "flow_clip"))

        return dem_clip, slope_clip, flow_direction_clip

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

    def _get_raster_dim(self, dem_clip):
        """
        Get raster spatial reference info.

        :param dem_clip: clipped dem raster map
        """
        dem_desc = arcpy.Describe(dem_clip)
        
        # lower left corner coordinates
        self.data['xllcorner'] = dem_desc.Extent.XMin
        self.data['yllcorner'] = dem_desc.Extent.YMin
        self.data['NoDataValue'] = dem_desc.noDataValue
        self.data['vpix'] = dem_desc.MeanCellHeight
        self.data['spix'] = dem_desc.MeanCellWidth
        self.data['pixel_area'] = self.data['spix'] * self.data['vpix']

        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dem'].shape[0]
        self.data['c'] = self.data['mat_dem'].shape[1]

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
                   self.data['mat_dem'][r][c] != self.data['NoDataValue'] and \
                   self.data['mat_dem'][r-1][c] != self.data['NoDataValue'] and \
                   self.data['mat_dem'][r+1][c] != self.data['NoDataValue'] and \
                   self.data['mat_dem'][r][c-1] != self.data['NoDataValue'] and \
                   self.data['mat_dem'][r][c+1] != self.data['NoDataValue']:

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

    def _get_slope_dir(self, dem_clip):
        """
        ?

        :param dem_clip:
        """

        # fiktivni vrstevnice a priprava "state cell, jestli to je tok
        # ci plocha
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dem_clip)
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

    def _prepare_streams(self, mask_shp, dem_clip, intersect):
        """

        :param mask_shp:
        :param dem_clip:
        :param intersect:
        """
        self.data['type_of_computing'] = 1

        ll_corner = arcpy.Point(
            self.data['xllcorner'], self.data['yllcorner']
        )

        # pocitam vzdy s ryhama pokud jsou zadane vsechny vstupy pro
        # vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [self._input_params['stream'],
                  self._input_params['table_stream_shape'],
                  self._input_params['table_stream_shape_code']]
        tflistin = [len(i) > 1 for i in listin]

        if all(tflistin):
            self.data['type_of_computing'] = 3

        if self.data['type_of_computing'] == 3 or \
           self.data['type_of_computing'] == 5:

            input = [self._input_params['stream'],
                     self._input_params['table_stream_shape'],
                     self._input_params['table_stream_shape_code'],
                     self._input_params['elevation'],
                     mask_shp,
                     self.data['spix'],
                     self.data['r'],
                     self.data['c'],
                     ll_corner,
                     self.data['outdir'],
                     dem_clip,
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

    def _join_table(self, in_data, in_field,
                    join_table, join_field, fields=None):
        """
        Join attribute table.

        :param in_data: input data layer
        :param in_field: input column
        :param join_table: table to join
        :param join_field: column to join
        :param fields: list of fields (None for all fields)
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

