import numpy as np
import math

import arcpy

from smoderp2d.core.general import GridGlobals, Globals
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

        arcpy.env.XYTolerance = "0.01 Meters"
        super(PrepareData, self).__init__(writter)

    def _create_AoI_outline(self, elevation, soil, vegetation):
        """See base method for description.
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

        aoi_mask = self.storage.output_filepath('aoi_mask')
        with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, cellSize=dem_mask, cellAlignment=dem_mask, snapRaster=dem_mask):
            field = arcpy.Describe(aoi_polygon).OIDFieldName
            arcpy.conversion.PolygonToRaster(aoi_polygon, field, aoi_mask, "MAXIMUM_AREA", "", GridGlobals.dy)

        # return aoi_polygon
        return aoi_polygon, aoi_mask

    def _create_DEM_derivatives(self, dem):
        """See base method for description.
        """
        # calculate the depressionless DEM
        dem_filled_path = self.storage.output_filepath('dem_filled')
        dem_filled = arcpy.sa.Fill(dem)
        dem_filled.save(dem_filled_path)

        # calculate the flow direction
        dem_flowdir_path = self.storage.output_filepath('dem_flowdir')
        flowdir = arcpy.sa.FlowDirection(dem_filled)
        flowdir.save(dem_flowdir_path)

        # calculate flow accumulation
        dem_flowacc_path = self.storage.output_filepath('dem_flowacc')
        flowacc = arcpy.sa.FlowAccumulation(flowdir)
        flowacc.save(dem_flowacc_path)

        # calculate slope
        dem_slope_path = self.storage.output_filepath('dem_slope')
        dem_slope = arcpy.sa.Slope(dem, "PERCENT_RISE")
        dem_slope.save(dem_slope_path)

        # calculate aspect
        dem_aspect_path = self.storage.output_filepath('dem_aspect')
        dem_aspect = arcpy.sa.Aspect(dem)
        dem_aspect.save(dem_aspect_path)

        return dem_filled_path, dem_flowdir_path, dem_flowacc_path, dem_slope_path, dem_aspect_path

    def _clip_raster_layer(self, dataset, aoi_polygon, name):
        """See base method for description.
        """
        output_path = self.storage.output_filepath(name)

        arcpy.management.Clip(dataset, out_raster=output_path, in_template_dataset=aoi_polygon, nodata_value=GridGlobals.NoDataValue, clipping_geometry="ClippingGeometry")

        #output_raster = arcpy.sa.ExtractByMask(dataset, aoi_polygon, analysis_extent = arcpy.Describe(aoi_polygon).Extent)
        #output_raster.save(output_path)

        return output_path

    def _clip_record_points(self, dataset, aoi_polygon, name):
        """See base method for description.
        """
        # create a feature layer for the selections
        points_layer = arcpy.management.MakeFeatureLayer(dataset, "points_layer")
        # select points inside the AIO
        arcpy.management.SelectLayerByLocation(points_layer, "WITHIN", aoi_polygon, "", "NEW_SELECTION")
        # save them as a new dataset
        points_clipped = self.storage.output_filepath(name)
        arcpy.management.CopyFeatures(points_layer, points_clipped)

        # select points outside the AoI
        # TODO: shouldn't be the point to close the border removed here as well?
        arcpy.management.SelectLayerByLocation(points_layer, "WITHIN", aoi_polygon, "", "NEW_SELECTION", "INVERT")
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
        """See base method for description.
        """
        return arcpy.RasterToNumPyArray(raster)

    def _update_grid_globals(self, reference):
        """See base method for description.
        """
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
# disabled by https://github.com/storm-fsv-cvut/smoderp2d/issues/150
#        inp = arcpy.Describe(self._input_params['elevation'])
#        if GridGlobals.dx != inp.meanCellWidth or GridGlobals.dy != inp.meanCellHeight:
#            raise DataPreparationInvalidInput(
#                "Input DEM spatial resolution ({}, {}) differs from processing "
#                "spatial resolution ({}, {})".format(GridGlobals.dx, GridGlobals.dy, inp.meanCellWidth, inp.meanCellHeight))

        # set arcpy environment (needed for rasterization)
        arcpy.env.extent = desc.Extent
        arcpy.env.snapRaster = reference

    def _compute_efect_cont(self, dem, asp):
        """See base method for description.
        """
        pii = math.pi / 180.0
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
                         aoi_polygon, table_soil_vegetation):
        """See base method for description.
        """
        # check if the soil_type and vegetation_type field names are
        # equal and deal with it if not
        if soil_type == vegetation_type:
            veg_fieldname = self.fieldnames['soilveg_type']
            Logger.info(
                "The vegetation type attribute field name ('{}') is equal to "
                "the soil type attribute field name. Vegetation type attribute "
                "will be renamed to '{}'.".format(vegetation_type, veg_fieldname)
            )
            # add the new field
            arcpy.management.AlterField(vegetation,
                                        vegetation_type, veg_fieldname)
        else:
            veg_fieldname = vegetation_type

        # create the geometric intersection of soil and vegetation layers
        soilveg_aoi_path = self.storage.output_filepath("soilveg_aoi")
        arcpy.analysis.Intersect([soil, vegetation, aoi_polygon], soilveg_aoi_path, "NO_FID")

        soilveg_code = self._input_params['table_soil_vegetation_code']
        if soilveg_code in arcpy.ListFields(soilveg_aoi_path):
            arcpy.management.DeleteField(soilveg_aoi_path, soilveg_code)
            Logger.info(
                "'{}' attribute field already in the table and will be replaced.".format(soilveg_code)
            )

        arcpy.management.AddField(soilveg_aoi_path, soilveg_code, "TEXT", field_length=15)

        # calculate "soil_veg" values (soil_type + vegetation_type)
        with arcpy.da.UpdateCursor(soilveg_aoi_path, [soil_type, veg_fieldname, soilveg_code]) as table:
            for row in table:
                row[2] = row[0] + row[1]
                table.updateRow(row)

        # join soil and vegetation model parameters from input table
        arcpy.management.JoinField(
            soilveg_aoi_path, soilveg_code,
            table_soil_vegetation,
            soilveg_code, list(self.soilveg_fields.keys())
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

        # generate numpy array of soil and vegetation attributes
        for field in self.soilveg_fields.keys():
            output = self.storage.output_filepath("soilveg_aoi_{}".format(field))
            aoi_mask = self.storage.output_filepath('aoi_mask')
            with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, cellSize=aoi_mask, cellAlignment=aoi_mask, snapRaster=aoi_mask):
                arcpy.conversion.PolygonToRaster(soilveg_aoi_path, field, output, "MAXIMUM_AREA", "", GridGlobals.dy)
            self.soilveg_fields[field] = self._rst2np(output)
            self._check_soilveg_dim(field)            

    def _get_points_location(self, points_layer):
        """See base method for description.
        """
        points_array = []
        if points_layer:
            # get number of points
            count = int(arcpy.management.GetCount(points_layer).getOutput(0))
            if count > 0:
                # get the points geometry and IDs into array
                desc = arcpy.Describe(points_layer)
                with arcpy.da.SearchCursor(points_layer, [desc.OIDFieldName, desc.ShapeFieldName]) as table:
                    i = 0
                    for row in table:
                        fid = row[0]
                        x, y = row[1]
                        if (self._get_points_dem_coords(x, y)):
                            r, c = self._get_points_dem_coords(x, y)
                            points_array.append([fid, r, c, x, y])
                        else:
                            Logger.info(
                            "Point FID = {} is at the edge of the raster. "
                            "This point will not be included in results.".format(fid))

                        i += 1
            else:
                raise DataPreparationInvalidInput(
                    "None of the record points lays within the modeled area."
                )
        return points_array
    
    def _stream_clip(self, stream, aoi_polygon):
        """See base method for description.
        """
        # AoI slighty smaller due to start/end elevation extraction
        aoi_buffer = arcpy.analysis.Buffer(aoi_polygon,
            self.storage.output_filepath('aoi_buffer'),
            -GridGlobals.dx / 3, 
            "FULL", "ROUND",
        )

        stream_aoi = self.storage.output_filepath('stream_aoi')
        arcpy.analysis.Clip(stream, aoi_buffer, stream_aoi)

        return stream_aoi

    def _stream_direction(self, stream, dem_aoi):
        """See base method for description.
        """
        segmentIDfieldName = self.fieldnames['stream_segment_id']
        startElevFieldName = self.fieldnames['stream_segment_start_elevation']
        endElevFieldName = self.fieldnames['stream_segment_end_elevation']
        inclinationFieldName = self.fieldnames['stream_segment_inclination']
        nextDownFieldName = self.fieldnames['stream_segment_next_down_id']
        segmentLengthFieldName = self.fieldnames['stream_segment_length']

        # add the streamID for later use
        arcpy.management.AddField(stream, segmentIDfieldName, "SHORT")
        sID = 1
        with arcpy.da.UpdateCursor(stream, [segmentIDfieldName]) as segments:
            for row in segments:
                row[0] = sID
                segments.updateRow(row)
                sID += 1

        # extract elevation for the stream segment vertices
        arcpy.ddd.InterpolateShape(dem_aoi, stream, self.storage.output_filepath("stream_Z"), "", "", "LINEAR", "VERTICES_ONLY")
        desc = arcpy.Describe(self.storage.output_filepath("stream_Z"))
        shapeFieldName = "SHAPE@"
        lengthFieldName = desc.LengthFieldName

        # segments properties
        segmentProps = {}
        # first points of segments to find the nextDownID
        firstPoints = {}
        with arcpy.da.SearchCursor(self.storage.output_filepath("stream_Z"), [shapeFieldName, segmentIDfieldName, lengthFieldName]) as segments:
            for row in segments:
                startpt = row[0].firstPoint
                endpt = row[0].lastPoint
                # negative elevation change is the correct direction for stream segments
                elevchange = endpt.Z - startpt.Z

                if elevchange == 0:
                    raise DataPreparationError(
                        'Stream segment '+segmentIDfieldName+': {} has zero slope'.format(row[1]))
                if elevchange < 0:
                    firstPoints.update({row[1]: startpt})
                else:
                    firstPoints.update({row[1]: endpt})

                inclination = elevchange/row[2]
                segmentProps.update({row[1]:{"startZ": startpt.Z, "endZ": endpt.Z, "inclination": inclination}})

        # add new fields to the stream segments feature class
        arcpy.management.AddField(stream, segmentIDfieldName, "SHORT")
        arcpy.management.AddField(stream, startElevFieldName, "DOUBLE")
        arcpy.management.AddField(stream, endElevFieldName, "DOUBLE")
        arcpy.management.AddField(stream, inclinationFieldName, "DOUBLE")
        arcpy.management.AddField(stream, nextDownFieldName, "DOUBLE")
        arcpy.management.AddField(stream, segmentLengthFieldName, "DOUBLE")

        XYtolerance = 0.01 # don't know why the arcpy.env.XYtolerance does not work (otherwise would use the arcpy.Point.equals() method)
        with arcpy.da.UpdateCursor(stream, [segmentIDfieldName, shapeFieldName, startElevFieldName, endElevFieldName, inclinationFieldName, nextDownFieldName,
                                            segmentLengthFieldName, lengthFieldName]) as table:
            for row in table:
                segmentInclination = segmentProps.get(row[0]).get("inclination")
                row[1] = row[1] if segmentInclination < 0 else self._reverse_line_direction(row[1])
                row[2] = segmentProps.get(row[0]).get("startZ")
                row[3] = segmentProps.get(row[0]).get("endZ")
                row[4] = -segmentInclination if segmentInclination < 0 else segmentInclination
                row[6] = row[7]

                # find the next down segment by comparing the points distance
                nextDownID = Globals.streamsNextDownIdNoSegment
                matched = []
                for segID in firstPoints.keys():
                    dist = pow(pow(row[1].lastPoint.X-firstPoints.get(segID).X, 2)+pow(row[1].lastPoint.Y-firstPoints.get(segID).Y, 2), 0.5)
                    if (dist < XYtolerance):
                        nextDownID = segID
                        matched.append(segID)
                if len(matched) > 1:
                    row[5] = None
                    raise DataPreparationError(
                        'Incorrect stream network topology downstream segment streamID: {}. The network can not bifurcate.'.format(row[0])
                    )
                else:
                    row[5] = nextDownID
                table.updateRow(row)


    def _reverse_line_direction(self, line):
        """Flips the order of points if a line to change its direction
        If the geometry is multipart the parts are dissolved into single part line

        :param line: line geometry to be flipped
        :return: the line geometry with flipped point order
        """
        newpart = []
        for part in line:
            for point in part:
                newpart.append(point)

        newline = arcpy.Polyline(arcpy.Array(reversed(newpart)))
        return newline

    def _stream_reach(self, stream):
        """See base method for description.
        """
        stream_seg = self.storage.output_filepath('stream_seg')
        arcpy.conversion.PolylineToRaster(stream, self.fieldnames['stream_segment_id'], stream_seg,
            "MAXIMUM_LENGTH", cellsize=GridGlobals.dx
        )

        mat_stream_seg = self._rst2np(stream_seg)
        # ML: is no_of_streams needed (-> mat_stream_seg.max())
        self._get_mat_stream_seg(mat_stream_seg)

        return mat_stream_seg.astype('int16')

    def _stream_shape(self, streams, channel_shape_code, channel_properties_table):
        """See base method for description.
        """
        if channel_shape_code not in self._get_field_names(streams):
            raise DataPreparationError(
                "Error joining channel shape properties to stream network segments!\n"
                "Check fields names in stream network feature class. "
                "Missing field is: '{}'".format(self._input_params['streams_channel_shape_code'])
            )

        arcpy.management.JoinField(streams, channel_shape_code, channel_properties_table, channel_shape_code,
            self.stream_shape_fields)

        stream_attr = self._get_streams_attr_()
        fields = list(stream_attr.keys())
        with arcpy.da.SearchCursor(streams, fields) as cursor:
            try:
                for row in cursor:
                    i = 0
                    for i in range(len(row)):
                        if row[i] in (" ", None):
                            raise DataPreparationError(
                                "Empty value in {} ({}) found.".format(self._input_params["channel_properties_table"], fields[i])
                            )
                        stream_attr[fields[i]].append(row[i])
                        i += 1

            except RuntimeError as e:
                raise DataPreparationError(
                        "Error: {}\n" 
                        "Check fields names in {}. "
                        "Proper columns codes are: {}".format(e, self._input_params["channel_properties_table"], self.stream_shape_fields)
                )

        return self._decode_stream_attr(stream_attr)

    def _check_input_data(self):
        """See base method for description.
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

        self._check_input_data_()

        _check_empty_values(
            self._input_params['vegetation'],
            self._input_params['vegetation_type']
        )
        _check_empty_values(
            self._input_params['soil'],
            self._input_params['soil_type']
        )

        # check presence of needed fields in stream shape properties table
        if self._input_params['channel_properties_table']:
            fields = self._get_field_names(self._input_params['channel_properties_table'])
            for f in self.stream_shape_fields:
                if f not in fields:
                    raise DataPreparationInvalidInput(
                        "Field '{}' not found in <{}>\nNeeded fields are: {}".format(
                            f, self._input_params['channel_properties_table'], ', '.join(map(lambda x: "'{}'".format(x), self.stream_shape_fields)))
                    )

    def _get_field_names(self, fc):
        return [field.name for field in arcpy.ListFields(fc)]
        # ML: what else?
                
