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
#from smoderp2d.providers.base.exceptions import LicenceNotAvailable

from smoderp2d.providers.arcgis.terrain import compute_products
from smoderp2d.providers.arcgis.manage_fields import ManageFields

class PrepareData(PrepareDataBase, ManageFields):
    def __init__(self, options, writter):
        super(PrepareData, self).__init__(writter)

        # setting the workspace environment
        arcpy.env.workspace = arcpy.GetParameterAsText(9)

        # checking if ArcGIS Spatial extension is available
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            self._add_message(self, "Spatial extension for ArcGIS not available - can not continue.")
            #raise LicenceNotAvailable("Spatial Analysis extension for ArcGIS is not available")


        # get input parameters
        self._get_input_params(options)

    def _get_input_params(self, options):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params = options
        # cast some options to float
        for opt in ('maxdt', 'end_time'):
            self._input_params[opt] = float(self._input_params[opt])

    def _add_message(self, message):
        """
        Pops up a message into arcgis and saves it into log file.
        :param message: Message to be printed.
        """
        #arcpy.AddMessage(message)
        Logger.info(message)


    def _set_output(self):
        """Creates empty output and temporary directories to which created
        files are saved. Creates temporary ArcGIS File Geodatabase.

        """
        super(PrepareData, self)._set_output()
        self.storage.create_storage(self._input_params['output'])

    def _create_AoI_outline(self):
        """
        Creates geometric intersection of input DEM, slope raster*, soil definition and landuse definition that will be used as Area of Interest outline
        *slope is not created yet, but generally the edge pixels have nonsense values so "one pixel shrinked DEM" extent is used instead

        :return: string path to AIO polygon feature class
        """
        dem_slope_mask_path = self.storage.output_filepath('dem_slope_mask')
        dem_mask = arcpy.sa.Reclassify( self._input_params['elevation'], "VALUE", "-100000 100000 1", "DATA")
        dem_slope_mask = arcpy.sa.Shrink(dem_mask, 1, 1)
        # the slope raster extent will be used in further intersections as it is always smaller then the DEM extent ...
        dem_slope_mask.save(dem_slope_mask_path)

        dem_polygon = self.storage.output_filepath('dem_polygon')
        arcpy.conversion.RasterToPolygon(dem_slope_mask, dem_polygon, "NO_SIMPLIFY", "VALUE")
        #self.storage.output_filepath('soil_boundary')
        dem_soil_veg_intersection = self.storage.output_filepath('AoI')
        arcpy.analysis.Intersect([dem_polygon, self._input_params['soil'], self._input_params['vegetation']], dem_soil_veg_intersection, "NO_FID")

        AoI_outline = self.storage.output_filepath('AoI_polygon')
        arcpy.management.Dissolve(dem_soil_veg_intersection, AoI_outline)

        if (int(arcpy.management.GetCount(AoI_outline).getOutput(0)) == 0):
            raise DataPreparationInvalidInput(
                "The input layers are not correct!"
                "The geometrical intersection of input datasets is empty.")
            return None
        else:
            self.AoI_outline = AoI_outline
            return AoI_outline


    def _create_DEM_derivatives(self):
        """
        Creates all the needed DEM derivatives in the DEM's original extent to avoid raster edge effects.
        # the clipping extent could be replaced be AOI border buffered by 1 cell to prevent time consuming operations on DEM if the DEM is much larger then the AOI
        """
        inputDEM = self._input_params['elevation']
        # calculate the depressionless DEM
        dem_filled_path = self.storage.output_filepath('dem_filled')
        dem_filled = arcpy.sa.Fill(inputDEM)
        dem_filled.save(dem_filled_path)

        # calculate the flow direction
        dem_flowdir_path = self.storage.output_filepath('dem_flowdir')
        flowdir = arcpy.sa.FlowDirection(inputDEM)
        flowdir.save(dem_flowdir_path)

        dem_flowacc_path = self.storage.output_filepath('dem_flowacc')
        flowacc = arcpy.sa.FlowAccumulation(flowdir)
        flowacc.save(dem_flowacc_path)

        # calculate slope
        dem_slope_path = self.storage.output_filepath('dem_slope')
        dem_slope = arcpy.sa.Slope(dem_filled, "PERCENT_RISE", 1)
        dem_slope.save(dem_slope_path)

        # calculate aspect
        dem_aspect_path = self.storage.output_filepath('dem_aspect')
        dem_aspect = arcpy.sa.Aspect(dem_filled, "", "")
        dem_aspect.save(dem_aspect_path)

        return dem_filled_path, dem_flowdir_path, dem_flowacc_path, dem_slope_path, dem_aspect_path


    def _clip_raster_layer(self, dataset, outline, noDataValue, name):
        """
        Clips raster dataset to given polygon.

        :param dataset: raster dataset to be clipped
        :param outline: feature class to be used as the clipping geometry
        :param noDataValue: raster value to be used outside the AoI
        :param name: dataset name in the _data dictionary

        :return: full path to clipped raster
        """

        output_path = self.storage.output_filepath(name)
        arcpy.management.Clip(dataset, "", output_path, outline, noDataValue, "ClippingGeometry")
        return output_path

    def _clip_record_points(self, dataset, outline, name):
        """
        Makes a copy of record points inside the AOI as new feature class and logs those outside AOI

        :param dataset: points dataset to be clipped
        :param outline: polygon feature class of the AoI
        :param name: output dataset name in the _data dictionary

        :return: full path to clipped points dataset
        """
        # create a feature layer for the selections
        points_layer = arcpy.management.MakeFeatureLayer(dataset, "points_layer")
        # select points inside the AIO
        arcpy.management.SelectLayerByLocation(points_layer, "WITHIN", outline, "", "NEW_SELECTION")
        # save them as a new dataset
        arcpy.management.CopyFeatures(points_layer, self.storage.output_filepath(name))

        # select points outside the AoI
        # TODO: shouldn't be the point to close the border removed here as well?
        arcpy.management.SelectLayerByLocation(points_layer, "WITHIN", outline, "", "NEW_SELECTION", "INVERT")
        numOutside = int(arcpy.management.GetCount(points_layer).getOutput(0))
        pointsOID = arcpy.Describe(dataset).OIDFieldName
        outsideList = []
        outsideListString = ""
        # get their IDs
        with arcpy.da.SearchCursor(points_layer, [pointsOID]) as table:
            for row in table:
                outsideList.append(row[0])
                if (len(outsideListString) == 0):
                    outsideListString = str(row[0])
                else:
                    outsideListString += ", "+str(row[0])
        # report them to the user
        self._add_message("     "+str(numOutside)+" record points outside of the area of interest ("+pointsOID+": "+outsideListString+")")

        return self.storage.output_filepath(name)

    def _prepare_soilveg(self):
        """
        Prepares the combination of soils and vegetation input layers.
        Gets the spatial intersection of both and checks the consistency of attribute table.

        :return: full path to soil and vegetation dataset
        """

        self._check_empty_values(self._input_params['vegetation'], self._input_params['vegetation_type'])
        self._check_empty_values(self._input_params['soil'], self._input_params['soil_type'])

        soilveg_aoi_path = self.storage.output_filepath("soilveg_aoi")

        # check if the soil_type and vegetation_type field names are equal and deal with it if not
        if (self._input_params['soil_type'] == self._input_params['vegetation_type']):
            Logger.info("The vegetation type attribute field name ('"+self._input_params['vegetation_type']+"') is equal to the soil type attribute field name.("
                "'"+self._input_params['soil_type']+"')! '"+self._input_params['vegetation_type']+"' will be renamed to '"+self.veg_fieldname+"'.")
            # add the new field
            arcpy.management.AddField(self._input_params['vegetation'], self._data['veg_type'], "TEXT", "", "", "15", "", "NULLABLE", "NON_REQUIRED", "")
            # copy the values
            with arcpy.da.UpdateCursor(self._input_params['vegetation'], [self._input_params['vegetation_type'], self.veg_fieldname]) as table:
                for row in table:
                    row[1] = row[0]
                    table.updateRow(row)
            # and remove the original field
            arcpy.management.DeleteField(self._input_params['vegetation'], self._input_params['vegetation_type'])
        else:
            self.veg_fieldname = self._input_params['vegetation_type']

        # create the geometric intersection of soil and vegetation layers
        arcpy.analysis.Intersect([self._input_params['soil'], self._input_params['vegetation'], self.AoI_outline], soilveg_aoi_path, "NO_FID")

        if self._data['soil_veg_fieldname'] in arcpy.ListFields(soilveg_aoi_path):
            arcpy.management.DeleteField(soilveg_aoi_path, self._data['soil_veg_fieldname'])
            Logger.info("'"+self._data['soil_veg_fieldname']+"' attribute field already in the table and will be replaced.")

        arcpy.management.AddField(soilveg_aoi_path, self._data['soil_veg_fieldname'], "TEXT", "", "", "15", "", "NULLABLE", "NON_REQUIRED","")

        # calculate "soil_veg" values (soil_type + vegetation_type)
        with arcpy.da.UpdateCursor(soilveg_aoi_path, [self._input_params['soil_type'], self.veg_fieldname, self._data['soil_veg_fieldname']]) as table:
            for row in table:
                row[2] = row[0] + row[1]
                table.updateRow(row)

        # join soil and vegetation model parameters from input table
        arcpy.management.JoinField(soilveg_aoi_path, self._data['soil_veg_fieldname'], self._input_params['table_soil_vegetation'], self._data['soil_veg_fieldname'], self._data['sfield'])

        # check for empty values
        with arcpy.da.SearchCursor(soilveg_aoi_path, self._data['sfield']) as cursor:
            row_id = 0
            for row in cursor:
                row_id += 1
                for i in range(len(row)):
                    if row[i] in ("", " ", None):
                        raise DataPreparationInvalidInput(
                            "Values in soilveg table are not correct "
                            "(field '{}': empty value found in row {})".format(self._data['sfield'][i], row_id))
        return soilveg_aoi_path

    def _check_empty_values(self, table, field):
        """
        Checks for empty (None or empty string) values in attribute field 'field' in table 'table'

        :param table: table to be searched in
        :param field: attribute field to be checked for empty values

        :return: true if no empty values found else false
        """
        oidfn = arcpy.Describe(table).OIDFieldName
        with arcpy.da.SearchCursor(table, [field, oidfn]) as cursor:
            for row in cursor:
                if row[0] in (None, ""):
                    self._add_message("'"+field+"' values in '"+table+"' table are not correct, empty value found in row {})".format(row[1]))
                    raise DataPreparationInvalidInput(
                        "'"+field+"' values in '"+table+"' table are not correct, "
                        "empty value found in row {})".format(row[1]))
                    return None

    def _get_soilveg_attribs(self, sfield, intersect):
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
