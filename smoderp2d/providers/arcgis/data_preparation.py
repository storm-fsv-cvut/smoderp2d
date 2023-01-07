import numpy as np
import math

import arcpy

from smoderp2d.core.general import GridGlobals
from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.base.exceptions import DataPreparationError, DataPreparationInvalidInput, LicenceNotAvailable
import smoderp2d.processes.rainfall as rainfall

class PrepareData(PrepareDataBase):
    def __init__(self, options, writter):
        # define input parameters
        self._set_input_params(options)

        # checking if ArcGIS Spatial extension is available
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            raise LicenceNotAvailable("Spatial Analysis extension for ArcGIS is not available")

        super(PrepareData, self).__init__(writter)

    def _create_AoI_outline(self, elevation, soil, vegetation):
        """Creates geometric intersection of input DEM, soil
        definition and landuse definition that will be used as Area of
        Interest outline. Slope is not created yet, but generally the
        edge pixels have nonsense values so "one pixel shrinked DEM"
        extent is used instead.

        :param elevation: string path to DEM layer
        :param soil: string path to soil definition layer
        :param vegetation: string path to vegenatation definition layer
        
        :return: string path to AIO polygon layer

        """
        dem_slope_mask_path = self.storage.output_filepath('dem_slope_mask')
        dem_mask = arcpy.sa.Reclassify(elevation, "VALUE", "-100000 100000 1", "DATA")
        dem_slope_mask = arcpy.sa.Shrink(dem_mask, 1, 1)
        # the slope raster extent will be used in further intersections as it is always smaller then the DEM extent ...
        dem_slope_mask.save(dem_slope_mask_path)

        dem_polygon = self.storage.output_filepath('dem_polygon')
        arcpy.conversion.RasterToPolygon(dem_slope_mask, dem_polygon, "NO_SIMPLIFY", "VALUE")
        aoi = self.storage.output_filepath('aoi')
        arcpy.analysis.Intersect([dem_polygon, soil, vegetation], aoi, "NO_FID")

        aoi_polygon = self.storage.output_filepath('aoi_polygon')
        arcpy.management.Dissolve(aoi, aoi_polygon)

        if int(arcpy.management.GetCount(aoi_polygon).getOutput(0)) == 0:
            raise DataPreparationInvalidInput(
                "The input layers are not correct! "
                "The geometrical intersection of input datasets is empty.")

        return aoi_polygon

    def _create_DEM_derivatives(self, dem):
        """Creates all the needed DEM derivatives in the DEM's
        original extent to avoid raster edge effects. The clipping
        extent could be replaced be AOI border buffered by 1 cell to
        prevent time consuming operations on DEM if the DEM is much
        larger then the AOI.

        :param dem: string path to DEM layer
        """
        # calculate the depressionless DEM
        dem_filled_path = self.storage.output_filepath('dem_filled')
        dem_filled = arcpy.sa.Fill(dem)
        dem_filled.save(dem_filled_path)

        # calculate the flow direction
        # ML: calculted from original DEM ?
        # ML: where is flowdir and flowacc / slope and aspect used?
        dem_flowdir_path = self.storage.output_filepath('dem_flowdir')
        flowdir = arcpy.sa.FlowDirection(dem)
        flowdir.save(dem_flowdir_path)

        # calculate flow accumulation
        dem_flowacc_path = self.storage.output_filepath('dem_flowacc')
        flowacc = arcpy.sa.FlowAccumulation(flowdir)
        flowacc.save(dem_flowacc_path)

        # calculate slope
        dem_slope_path = self.storage.output_filepath('dem_slope')
        dem_slope = arcpy.sa.Slope(dem_filled, "PERCENT_RISE")
        dem_slope.save(dem_slope_path)

        # calculate aspect
        dem_aspect_path = self.storage.output_filepath('dem_aspect')
        dem_aspect = arcpy.sa.Aspect(dem_filled)
        dem_aspect.save(dem_aspect_path)

        return dem_filled_path, dem_flowdir_path, dem_flowacc_path, dem_slope_path, dem_aspect_path

    def _clip_raster_layer(self, dataset, outline, name):
        """Clips raster dataset to given polygon.

        :param dataset: raster dataset to be clipped
        :param outline: feature class to be used as the clipping geometry
        :param name: dataset name in the _data dictionary

        :return: full path to clipped raster
        """
        output_path = self.storage.output_filepath(name)
        arcpy.management.Clip(dataset, out_raster=output_path, in_template_dataset=outline,
                              nodata_value=GridGlobals.NoDataValue, clipping_geometry="ClippingGeometry")
        return output_path

    def _clip_record_points(self, dataset, outline, name):
        """Makes a copy of record points inside the AOI as new
        feature layer and logs those outside AOI.

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
        points_clipped = self.storage.output_filepath(name)
        arcpy.management.CopyFeatures(points_layer, points_clipped)

        # select points outside the AoI
        # TODO: shouldn't be the point to close the border removed here as well?
        arcpy.management.SelectLayerByLocation(points_layer, "WITHIN", outline, "", "NEW_SELECTION", "INVERT")
        pointsOID = arcpy.Describe(dataset).OIDFieldName
        outsideList = []
        # get their IDs
        with arcpy.da.SearchCursor(points_layer, [pointsOID]) as table:
            for row in table:
                outsideList.append(row[0])

        # report them to the user
        Logger.info("\t{} record points outside of the area of interest ({}: {})".format(
            len(outsideList), pointsOID, ",".join(map(str, outsideList)))
        )

        return points_clipped

    def _rst2np(self, raster):
        """Convert raster data into numpy array.

        :param raster: raster name

        :return: numpy array
        """
        return arcpy.RasterToNumPyArray(raster)

    def _update_raster_dim(self, reference):
        """Update raster spatial reference info.

        This function must be called before _rst2np() is used first
        time.

        :param reference: reference raster layer
        """
        # size of the raster [0] = number of rows; [1] = number of columns
        GridGlobals.r = self.data['mat_dem'].shape[0]
        GridGlobals.c = self.data['mat_dem'].shape[1]

        desc = arcpy.Describe(reference)

        # check data consistency
        if desc.height != GridGlobals.r or \
                desc.width != GridGlobals.c:
            raise DataPreparationError(
                "Data inconsistency ({},{}) vs ({},{})".format(
                    desc.height, desc.width,
                    GridGlobals.r, GridGlobals.c)
            )

        # lower left corner coordinates
        GridGlobals.set_llcorner((desc.Extent.XMin, desc.Extent.YMin))
        GridGlobals.set_size((desc.MeanCellWidth, desc.MeanCellHeight))

        # set arcpy environment (needed for rasterization)
        arcpy.env.extent = reference
        arcpy.env.snapRaster = reference

    def _compute_efect_cont(self, dem_clip):
        """
        Compute efect contour array.
        ML: improve description
        
        :param dem_clip: string to dem clipped by area of interest

        :return: numpy array
        """
        pii = math.pi / 180.0
        asp = arcpy.sa.Aspect(dem_clip)
        asppii = arcpy.sa.Times(asp, pii)
        sinasp = arcpy.sa.Sin(asppii)
        cosasp = arcpy.sa.Cos(asppii)
        sinslope = arcpy.sa.Abs(sinasp)
        cosslope = arcpy.sa.Abs(cosasp)
        times1 = arcpy.sa.Plus(cosslope, sinslope)
        times1.save(self.storage.output_filepath('ratio_cell'))

        efect_cont = arcpy.sa.Times(times1, GridGlobals.dx)
        efect_cont.save(self.storage.output_filepath('efect_cont'))
        
        return self._rst2np(efect_cont)

    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_outline, table_soil_vegetation):
        """Prepares the combination of soils and vegetation input
        layers. Gets the spatial intersection of both and checks the
        consistency of attribute table.

        :param soil: string path to soil layer
        :param soil_type: soil type attribute
        :param vegetation: string path to vegetation layer
        :param vegetation_type: vegetation type attribute
        :param aoi_outline: string path to polygon layer defining area of interest
        :param table_soil_vegetation: string path to table with soil and vegetation attributes
        
        :return: full path to soil and vegetation dataset
        """
        soilveg_aoi_path = self.storage.output_filepath("soilveg_aoi")

        # check if the soil_type and vegetation_type field names are
        # equal and deal with it if not
        if soil_type == vegetation_type:
            veg_fieldname = 'veg_type'
            Logger.info(
                "The vegetation type attribute field name ('{}') is equal to "
                "the soil type attribute field name. Vegetation type attribute "
                "will be renamed to '{}'.".format(vegatation_type, veg_type)
            )
            # add the new field
            arcpy.management.AlterField(vegetation,
                                        vegetation_type, veg_fieldname)
        else:
            veg_fieldname = vegetation_type

        # create the geometric intersection of soil and vegetation layers
        arcpy.analysis.Intersect([soil, vegetation, aoi_outline], soilveg_aoi_path, "NO_FID")

        if self._input_params['table_soil_vegetation_code'] in arcpy.ListFields(soilveg_aoi_path):
            arcpy.management.DeleteField(soilveg_aoi_path, self._input_params['table_soil_vegetation_code'])
            Logger.info("'{}' attribute field already in the table and will be replaced.".format(self._input_params['table_soil_vegetation_code']))

        arcpy.management.AddField(soilveg_aoi_path, self._input_params['table_soil_vegetation_code'], "TEXT", "", "", "15", "", "NULLABLE", "NON_REQUIRED","")

        # calculate "soil_veg" values (soil_type + vegetation_type)
        with arcpy.da.UpdateCursor(soilveg_aoi_path, [soil_type, veg_fieldname, self._input_params['table_soil_vegetation_code']]) as table:
            for row in table:
                row[2] = row[0] + row[1]
                table.updateRow(row)

        # join soil and vegetation model parameters from input table
        arcpy.management.JoinField(
            soilveg_aoi_path, self._input_params['table_soil_vegetation_code'],
            table_soil_vegetation,
            self._input_params['table_soil_vegetation_code'], list(self.soilveg_fields.keys())
        )

        # check for empty values
        with arcpy.da.SearchCursor(soilveg_aoi_path, list(self.soilveg_fields.keys())) as cursor:
            row_id = 0
            for row in cursor:
                row_id += 1
                for i in range(len(row)):
                    if row[i] in ("", " ", None):
                        raise DataPreparationInvalidInput(
                            "Values in soilveg table are not correct "
                            "(field '{}': empty value found in row {})".format(self.sfield[i], row_id)
                        )

        # Generate numpy array of soil and vegetation attributes.
        for field in self.soilveg_fields.keys():
            output = self.storage.output_filepath("soilveg_aoi_{}".format(field))
            arcpy.conversion.PolygonToRaster(soilveg_aoi_path, field, output, "MAXIMUM_AREA", "", GridGlobals.dy)
            self.soilveg_fields[field] = self._rst2np(output)
            if self.soilveg_fields[field].shape[0] != GridGlobals.r or \
                    self.soilveg_fields[field].shape[1] != GridGlobals.c:
                raise DataPreparationError(
                    "Unexpected array {} dimension {}: should be ({}, {})".format(
                        field, self.soilveg_fields[field].shape,
                        GridGlobals.r, GridGlobals.c)
                )

    def _get_array_points(self):
        """Get array of points. Points near AOI border are skipped.
        """
        array_points = None
        if self.data['points'] not in ("", "#", None):
            # get number of points
            count = int(arcpy.management.GetCount(self.data['points']).getOutput(0))
            if count > 0:
                # empty array
                array_points = np.zeros([int(count), 5], float)

                # get the points geometry and IDs into array
                desc = arcpy.Describe(self.data['points'])
                with arcpy.da.SearchCursor(self.data['points'], [desc.OIDFieldName, desc.ShapeFieldName]) as table:
                    i = 0
                    for row in table:
                        fid = row[0]
                        x, y = row[1]

                        self._get_array_points_(array_points, x, y, fid, i)
                        i += 1

        return array_points
    
    def _stream_clip(self, stream, aoi_polygon):
        """Clip stream with intersect of input data."""
        aoi_buffer = arcpy.analysis.Buffer(aoi_polygon,
            self.storage.output_filepath('aoi_buffer'),
            -GridGlobals.dx / 3, # ML: ? + clip ?
            "FULL", "ROUND",
        )

        stream_aoi = self.storage.output_filepath('stream_aoi')
        arcpy.analysis.Clip(stream, aoi_buffer, stream_aoi)

        return stream_aoi

    def _stream_direction(self, stream, dem_aoi):
        """
        Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.

        :param stream: vector stream features
        """
        # extract elevation for start/end stream nodes
        stream_start = arcpy.management.FeatureVerticesToPoints(
            stream, self.storage.output_filepath("stream_start"), "START"
        )
        stream_end = arcpy.management.FeatureVerticesToPoints(
            stream, self.storage.output_filepath("stream_end"), "END"
        )

        arcpy.sa.ExtractMultiValuesToPoints(
            stream_start, [[dem_aoi, "elev_start"]]
        )
        arcpy.sa.ExtractMultiValuesToPoints(
            stream_end, [[dem_aoi, "elev_end"]]
        )
        arcpy.management.AddXY(stream_start)
        arcpy.management.AddXY(stream_end)

        oid_field = arcpy.Describe(stream).OIDFieldName
        arcpy.management.JoinField(
            stream, oid_field,
            stream_start, arcpy.Describe(stream_start).OIDFieldName, ["elev_start", "POINT_X", "POINT_Y"]
        )
        arcpy.management.AlterField(stream_end, "POINT_X", "POINT_X_END")
        arcpy.management.AlterField(stream_end, "POINT_Y", "POINT_Y_END")
        arcpy.management.JoinField(
            stream, oid_field,
            stream_end, arcpy.Describe(stream_end).OIDFieldName, ["elev_end", "POINT_X_END", "POINT_Y_END"]
        )

        # flip stream
        with arcpy.da.SearchCursor(stream, [oid_field, "elev_start", "elev_end"]) as cursor:
            for row in cursor:
                if row[1] < row[2]:
                    arcpy.edit.FlipLine(stream) # ML: all streams vs one stream?

        # add to_node attribute
        arcpy.management.AddField(stream, "to_node", "DOUBLE")
        with arcpy.da.SearchCursor(stream, [oid_field, "POINT_X", "POINT_Y"]) as cursor_start:
            for row in cursor_start:
                start_pnt = (row[1], row[2])
                fid = row[0]

                with arcpy.da.UpdateCursor(stream, ["POINT_X_END", "POINT_Y_END", "to_node"]) as cursor_end:
                    for row in cursor_end:
                        end_pnt = (row[0], row[1])
                        if start_pnt == end_pnt:
                            row[2] = fid
                        else:
                            row[2] = GridGlobals.NoDataValue
                        cursor_end.updateRow(row)

    def _stream_reach(self, stream):
        """Get numpy array of integers detecting whether there is a stream on
        corresponding pixel of raster (number equal or greater than
        1000 in return numpy array) or not (number 0 in return numpy
        array).

        :param stream: Polyline with stream in the area.
        :return mat_stream_seg: Numpy array
        """
        stream_seg = self.storage.output_filepath('stream_seg')
        arcpy.conversion.PolylineToRaster(
            stream, arcpy.Describe(stream).OIDFieldName, stream_seg,
            "MAXIMUM_LENGTH", cellsize=GridGlobals.dx
        )

        mat_stream_seg = self._rst2np(stream_seg)
        # ML: is no_of_streams needed (-> mat_stream_seg.max())
        self._get_mat_stream_seg(mat_stream_seg)

        return mat_stream_seg.astype('int16')

    def _stream_slope(self, stream):
        """Compute slope of stream

        :param stream: stream layer
        """
        arcpy.management.AddField(stream, "slope", "DOUBLE")
        fields = [arcpy.Describe(stream).OIDFieldName,
                  "elev_start", "elev_end", "slope", "shape_length"]
        with arcpy.da.UpdateCursor(stream, fields) as cursor:
            for row in cursor:
                slope = (row[1] - row[2]) / row[4]
                if slope == 0:
                    raise DataPreparationError('Reach FID: {} has zero slope'.format(row[0]))
                row[3] = slope
                cursor.updateRow(row)

    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        """Compute shape of stream.

        :param stream: stream layer
        :param stream_shape_code: shape code column
        :param stream_shape_tab: table with stream shapes
        """
        arcpy.management.JoinField(
            stream, stream_shape_code,
            stream_shape_tab, stream_shape_code,
            self.stream_shape_fields
        )

        fid = arcpy.Describe(stream).OIDFieldName
        fields = [fid, 'point_x', 'point_y', 'point_x_end', 'point_y_end', 'to_node',
                'shape_length', 'slope', stream_shape_code, 'number', 'shapetype', 'b', 'm', 'roughness', 'q365']
        stream_attr = {}
        for f in fields:
            stream_attr[f] = []
        with arcpy.da.SearchCursor(stream, fields) as cursor:
            try:
                for row in cursor:
                    i = 0
                    for i in range(len(row)):
                        if row[i] == " " or row[i] is None:
                            raise DataPreparationError(
                                "Empty value in tab_stream_shape ({}) found.".format(fields[i])
                            )
                        stream_attr[fields[i]].append(row[i])
                        i += 1

            except RuntimeError as e:
                raise DataPreparationError(
                        "Error: {}\n" 
                        "Check if fields code in table_stream_shape are correct. "
                        "Proper columns codes are: {}".format(e, self.stream_shape_fields)
                )

        stream_attr['fid'] = stream_attr.pop(fid)

        return stream_attr

    def _check_input_data(self):
        """Check input data.

        Raise DataPreparationInvalidInput on error.
        """
        def _check_empty_values(table, field):
            oidfn = arcpy.Describe(table).OIDFieldName
            with arcpy.da.SearchCursor(table, [field, oidfn]) as cursor:
                for row in cursor:
                    if row[0] in (None, ""):
                        raise DataPreparationInvalidInput(
                            "'{}' values in '{}' table are not correct, "
                            "empty value found in row {})".format(field, table, row[1])
                        )
        
        _check_empty_values(
            self._input_params['vegetation'],
            self._input_params['vegetation_type']
        )
        _check_empty_values(
            self._input_params['soil'],
            self._input_params['soil_type']
        )

        if self._input_params['table_stream_shape']:
            fields = [f.name for f in arcpy.Describe(self._input_params['table_stream_shape']).fields]
            for f in self.stream_shape_fields:
                if f not in fields:
                    raise DataPreparationInvalidInput(
                        "Field '{}' not found in '{}'\nProper columns codes are: {}".format(
                            f, self._input_params['table_stream_shape'], self.stream_shape_fields)
                    )


        # ML: what else?
                
