import shutil
import os
import sys
import numpy as np
import math
import csv
import arcpy

import smoderp2d.processes.rainfall as rainfall

from smoderp2d.core.general import GridGlobals

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput

from smoderp2d.providers.arcgis import constants
from smoderp2d.providers.arcgis.terrain import compute_products
from smoderp2d.providers.arcgis.manage_fields import ManageFields

class PrepareData(PrepareDataBase, ManageFields):
    def __init__(self, writter):
        super(PrepareData, self).__init__(writter)

        # setting the workspace environment
        arcpy.env.workspace = arcpy.GetParameterAsText(9)

        # checking if ArcGIS Spatial extension is available
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            #raise Error...
            self._add_message(self, "Spatial extension for ArcGIS not available - can not continue.")

        # get input parameters
        self._get_input_params()

    def _get_input_params(self):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params = {
            # parameter indexes from the bin/arcgis/SMODERP2D.pyt tool for ArcGIS
            'elevation': arcpy.parameters[constants.PARAMETER_DEM].valueAsText,
            'soil': arcpy.parameters[constants.PARAMETER_SOIL].valueAsText,
            'soil_type': arcpy.parameters[constants.PARAMETER_SOIL_TYPE].valueAsText,
            'vegetation': arcpy.parameters[constants.PARAMETER_VEGETATION].valueAsText,
            'vegetation_type': arcpy.parameters[constants.PARAMETER_VEGETATION_TYPE].valueAsText,
            'rainfall_file': arcpy.parameters[constants.PARAMETER_PATH_TO_RAINFALL_FILE].valueAsText,
            'maxdt': float(arcpy.parameters[constants.PARAMETER_MAX_DELTA_T].valueAsText),
            'end_time': float(arcpy.parameters[constants.PARAMETER_END_TIME].valueAsText) * 60.0,  # convert input to seconds
            'points': arcpy.parameters[constants.PARAMETER_POINTS].valueAsText,
            'output': arcpy.parameters[constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY].valueAsText,
            'table_soil_vegetation': arcpy.parameters[constants.PARAMETER_SOILVEGTABLE].valueAsText,
            'table_soil_vegetation_code': arcpy.parameters[constants.PARAMETER_SOILVEGTABLE_CODE].valueAsText,
            'stream': arcpy.parameters[constants.PARAMETER_STREAM].valueAsText,
            'table_stream_shape': arcpy.parameters[constants.PARAMETER_STREAMTABLE].valueAsText,
            'table_stream_shape_code': arcpy.parameters[constants.PARAMETER_STREAMTABLE_CODE].valueAsText
        }

    def _add_message(self, message):
        """
        Pops up a message into arcgis and saves it into log file.
        :param message: Message to be printed.
        """
        arcpy.AddMessage(message)
        Logger.info(message)


    def _set_output(self):
        """Creates empty output and temporary directories to which created
        files are saved. Creates temporary ArcGIS File Geodatabase.

        """
        super(PrepareData, self)._set_output()
        self.storage.create_storage(self._input_params['output'])

    def _create_mask(self):
        """Set mask from elevation map.

        :return: dem copy, binary mask
        """
        # Do not work for CopyRaster, https://github.com/storm-fsv-cvut/smoderp2d/issues/46
        # dem_copy = os.path.join(self.data['temp'], 'dem_copy')
        # dem_copy = self.storage.output_filepath('dem_copy')
        #
        # arcpy.management.CopyRaster(
        #     self._input_params['elevation'], dem_copy
        # )

        # align computation region to DTM grid
        arcpy.env.snapRaster = self._input_params['elevation']
        arcpy.env.Extent = self._input_params['elevation']

        dem_mask = self.storage.output_filepath('dem_mask')
        arcpy.sa.Reclassify(
            self._input_params['elevation'], "VALUE", "-100000 100000 1", dem_mask, "DATA"
        )
        dem_polygon = os.path.join(self.data['temp'], 'dem_outline')
        arcpy.conversion.RasterToPolygon(dem_mask, dem_polygon, "NO_SIMPLIFY", "VALUE")

        dem_soil_veg_intersection = os.path.join(self.data['temp'], 'AOI')
        arcpy.analysis.Intersect([dem_polygon, self._input_params['soil'], self._input_params['vegetation']], dem_soil_veg_intersection, "NO_FID")

        return dem_soil_veg_intersection, dem_mask

    def _terrain_products(self, dem):
        """Computes terrains products.

        :param str elev: DTM raster map name
        
        :return: (filled elevation, flow direction, flow accumulation, slope)
        """
        flow_direction_clip, flow_accumulation_clip, slope_clip = compute_products(dem, self.data['outdir'])

        # this is a workaround if the input dem does not have nodatavalue assigned 
        # or has different nodatavalue compared to env nodatavalue. 
        slope_clip_desc = arcpy.Describe(slope_clip)
        self.data['NoDataValue'] = slope_clip_desc.nodatavalue
        return flow_direction_clip, flow_accumulation_clip, slope_clip 

    def _get_intersect(self, dem, mask, vegetation, soil, vegetation_type, soil_type, table_soil_vegetation, table_soil_vegetation_code):
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
        mask_shp = self.storage.output_filepath('vector_mask')
        arcpy.conversion.RasterToPolygon(mask, mask_shp, "NO_SIMPLIFY")

        # dissolve soil and vegetation polygons
        soil_boundary = self.storage.output_filepath('soil_boundary')
        vegetation_boundary = self.storage.output_filepath('vegetation_boundary')
        arcpy.management.Dissolve(vegetation, vegetation_boundary, vegetation_type)
        arcpy.management.Dissolve(soil, soil_boundary, soil_type)

        # do intersection
        group = [soil_boundary, vegetation_boundary, mask_shp]
        intersect = self.storage.output_filepath('inter_soil_lu')
        arcpy.analysis.Intersect(group, intersect, "ALL", "", "INPUT")

        # remove "soil_veg" if exists and create a new one
        if self._data['soil_veg_column'] in arcpy.ListFields(intersect):
            arcpy.management.DeleteField(intersect, self._data['soil_veg_column'])
            Logger.info("'"+self._data['soil_veg_column']+"' attribute field was replaced")
        arcpy.management.AddField(intersect, self._data['soil_veg_column'], "TEXT", "", "", "15", "", "NULLABLE", "NON_REQUIRED","")

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        fields = [soil_type, vtype1, self._data['soil_veg_column']]
        with arcpy.da.UpdateCursor(intersect, fields) as table:
            for row in table:
                row[2] = row[0] + row[1]
                table.updateRow(row)

        # copy attribute table to DBF file for modifications
        soil_veg_copy_dir = os.path.join(self.data['outdir'], self._data['soil_veg_copy'])
        arcpy.conversion.TableToTable(table_soil_vegetation, soil_veg_copy_dir, "soil_veg_tab_current.dbf")

        # join table copy to intersect feature class
        self._join_table(
            intersect, self._data['soil_veg_column'],
            soil_veg_copy,
            table_soil_vegetation_code,
            ";".join(self._data['sfield'])
        )

        # check for empty values
        with arcpy.da.SearchCursor(intersect, self._data['sfield']) as cursor:
            row_id = 0
            for row in cursor:
                row_id += 1
                for i in range(len(row)):
                    if row[i] in ("", " ", None): # TODO: empty string or NULL value?
                        raise DataPreparationInvalidInput(
                            "Values in soilveg tab are not correct "
                            "(field '{}': empty value found in row {})".format(self._data['sfield'][i], row_id))

        return intersect, mask_shp, self._data['sfield']

    def _clip_data(self, dem, intersect):
        """
        Clip input data based on AOI.

        :param str dem: raster DTM name
        :param str intersect: vector intersect feature call name

        :return str dem_clip: output clipped DTM name

        """
        if self.data['points']:
            self.data['points'] = self._clip_points(intersect)

        # set extent from intersect vector map
        arcpy.env.extent = intersect

        # raster description
        dem_desc = arcpy.Describe(dem)

        # output raster coordinate system
        arcpy.env.outputCoordinateSystem = dem_desc.SpatialReference

        # create raster mask based on intersect feature call
        mask = self.storage.output_filepath('inter_mask')
        arcpy.conversion.PolygonToRaster(
            intersect, self.storage.primary_key, mask, "MAXIMUM_AREA",
            cellsize = dem_desc.MeanCellHeight)

        # cropping rasters
        dem_clip = arcpy.sa.ExtractByMask(dem, mask)
        dem_clip.save(self.storage.output_filepath('dem_inter'))
        
        return dem_clip

    def _clip_points(self, intersect):
        """
        Clip input points data.

        :param intersect: vector intersect feature class
        """
        pointsClipCheck = self.storage.output_filepath('points_inter', item='')
        arcpy.Clip_analysis(
            self.data['points'], intersect, pointsClipCheck
        )

        # count number of features (rows)
        npoints = arcpy.GetCount_management(self._input_params['points'])
        npoints_clipped = arcpy.GetCount_management(pointsClipCheck)
                
        self._diff_npoints(int(npoints[0]), int(npoints_clipped[0]))

        return pointsClipCheck

    def _get_attrib(self, sfield, intersect):
        """
        Get numpy arrays of selected attributes.

        :param sfield: list of attributes
        :param intersect: vector intersect name

        :return all_atrib: list of numpy array
        """
        all_attrib = self._init_attrib(sfield, intersect)
        
        idx = 0
        for field in sfield:
            output = os.path.join(self.data['outdir'], self._data['sfield_dir'], "r{}".format(field))
            arcpy.conversion.PolygonToRaster(intersect, field, output, "MAXIMUM_AREA", "", self.data['dy'])
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
        GridGlobals.set_llcorner((dem_desc.Extent.XMin, dem_desc.Extent.YMin))
        self.data['xllcorner'] = dem_desc.Extent.XMin
        self.data['yllcorner'] = dem_desc.Extent.YMin
        GridGlobals.set_size((dem_desc.MeanCellHeight, dem_desc.MeanCellWidth))
        self.data['dy'] = dem_desc.MeanCellHeight
        self.data['dx'] = dem_desc.MeanCellWidth
        GridGlobals.set_pixel_area(self.data['dx'] * self.data['dy'])
        self.data['pixel_area'] = self.data['dx'] * self.data['dy']

        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dem'].shape[0]
        self.data['c'] = self.data['mat_dem'].shape[1]

    def _get_array_points(self):
        """Get array of points. Points near AOI border are skipped.
        """
        if (self.data['points'] not in("", "#", None)):
            # get number of points
            count = arcpy.management.GetCount(self.data['points']).getOutput(0)
            
            if count > 0:
                # identify the geometry field
                desc = arcpy.Describe(self.data['points'])
                shapefieldname = desc.ShapeFieldName

                # empty array
                self.data['array_points'] = np.zeros([int(count), 5], float)

                # get the points geometry and IDs into array
                with arcpy.da.SearchCursor(self.data['points'], [self.storage.primary_key, shapefieldname]) as table:
                    i = 0
                    for row in table:
                        fid = row[0]
                        # geometry
                        feature = row[1]
                        pnt = feature.getPart()

                        i = self._get_array_points_(pnt.X, pnt.Y, fid, i) # tak tomuhle nerozumim
                        # self.data['array_points'].append([pnt.X, pnt.Y, fid, i]) # nemelo to bejt neco jako tohle?
                        i += 1
            else:
                self.data['array_points'] = None
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
        sinslope = arcpy.sa.Abs(sinasp)
        cosslope = arcpy.sa.Abs(cosasp)
        times1 = arcpy.sa.Plus(cosslope, sinslope)
        times1.save(self.storage.output_filepath('ratio_cell'))

        efect_cont = arcpy.sa.Times(times1, self.data['dx'])
        efect_cont.save(self.storage.output_filepath('efect_cont'))
        self.data['mat_efect_cont'] = self._rst2np(efect_cont)

    def _streamPreparation(self, args):
        from smoderp2d.providers.arcgis.stream_preparation import StreamPreparation

        return StreamPreparation(args, writter=self.storage).prepare()

    def _check_input_data(self):
        """Check input data.
        """
        # TODO: not imlemented yet...
        pass
