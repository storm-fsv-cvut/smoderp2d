import os
import numpy as np
import math
import arcpy

from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataGISBase
from smoderp2d.providers.base.exceptions import DataPreparationError, \
    DataPreparationInvalidInput, LicenceNotAvailable, \
    DataPreparationNoIntersection


class PrepareData(PrepareDataGISBase):
    def __init__(self, options, writer):
        # define input parameters
        self._set_input_params(options)

        # checking if ArcGIS Spatial extension is available
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            raise LicenceNotAvailable(
                "Spatial Analysis extension for ArcGIS is not available"
            )

        arcpy.env.XYTolerance = "0.000001 Meters"  # increased because of GRASS GIS data comparison
        super(PrepareData, self).__init__(writer)

    def _create_AoI_outline(self, elevation, soil, vegetation):
        """See base method for description.
        """
        dem_slope_mask_path = self.storage.output_filepath('dem_slope_mask')
        dem_mask = arcpy.sa.Reclassify(
            elevation, "VALUE", "-100000 100000 1", "DATA"
        )
        dem_slope_mask = arcpy.sa.Shrink(dem_mask, 1, 1)
        # the slope raster extent will be used in further
        # intersections as it is always smaller than the DEM extent
        # ...
        dem_slope_mask.save(dem_slope_mask_path)

        dem_polygon = self.storage.output_filepath('dem_polygon')
        arcpy.conversion.RasterToPolygon(
            dem_slope_mask, dem_polygon, "NO_SIMPLIFY", "VALUE"
        )
        aoi = self.storage.output_filepath('aoi')
        arcpy.analysis.Intersect(
            [dem_polygon, soil, vegetation], aoi, "NO_FID"
        )

        aoi_polygon_mem = os.path.join("in_memory", "aoi_polygon")
        arcpy.management.Dissolve(aoi, aoi_polygon_mem)

        if int(arcpy.management.GetCount(aoi_polygon_mem).getOutput(0)) == 0:
            raise DataPreparationNoIntersection()

        aoi_mask_mem = os.path.join("in_memory", "aoi_mask")
        with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, cellSize=dem_mask, cellAlignment=dem_mask, snapRaster=dem_mask):
            field = arcpy.Describe(aoi_polygon_mem).OIDFieldName
            arcpy.conversion.PolygonToRaster(
                aoi_polygon_mem, field, aoi_mask_mem, "MAXIMUM_AREA"
            )

        # perform aoi_mask postprocessing - remove no-data cells on the edges
        arcpy.conversion.RasterToPolygon(aoi_mask_mem, aoi_polygon_mem, "NO_SIMPLIFY")
        aoi_mask = self.storage.output_filepath('aoi_mask')
        with arcpy.EnvManager(extent=aoi_polygon_mem):
            arcpy.management.Clip(aoi_mask_mem, out_raster=aoi_mask, nodata_value=GridGlobals.NoDataValue,
                                  in_template_dataset=aoi_polygon_mem, clipping_geometry="ClippingGeometry")
        # generate aoi_polygon to be snapped to aoi_mask
        aoi_polygon = self.storage.output_filepath('aoi_polygon')
        with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, extent=aoi_mask, cellSize=aoi_mask, cellAlignment=aoi_mask,
                              snapRaster=aoi_mask):
            arcpy.conversion.RasterToPolygon(aoi_mask, aoi_polygon, "NO_SIMPLIFY")
        arcpy.env.extent = aoi_polygon

        return aoi_polygon, aoi_mask

    def _create_DEM_derivatives(self, dem):
        """See base method for description.
        """
        with arcpy.EnvManager(extent=dem):
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

        return (
            dem_filled_path, dem_flowdir_path, dem_flowacc_path,
            dem_slope_path, dem_aspect_path
        )

    def _clip_raster_layer(self, dataset, aoi_mask, name):
        """See base method for description.
        """
        output_path = self.storage.output_filepath(name)
        # arcpy.management.Clip(dataset, out_raster=output_path, in_template_dataset=aoi_polygon, nodata_value=GridGlobals.NoDataValue, clipping_geometry="ClippingGeometry")
        with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, cellSize=aoi_mask, cellAlignment=aoi_mask, snapRaster=aoi_mask):
            output_raster = arcpy.sa.ExtractByMask(dataset, aoi_mask)
            # analysis_extent = arcpy.Describe(aoi_mask).Extent)
            output_raster.save(output_path)
        return output_path

    def _clip_record_points(self, dataset, aoi_polygon, name):
        """See base method for description.
        """
        # create a feature layer for the selections
        points_layer = arcpy.management.MakeFeatureLayer(
            dataset, "points_layer"
        )
        # select points inside the AIO
        arcpy.management.SelectLayerByLocation(
            points_layer, "WITHIN", aoi_polygon, "", "NEW_SELECTION"
        )
        # save them as a new dataset
        points_clipped = self.storage.output_filepath(name)
        arcpy.management.CopyFeatures(points_layer, points_clipped)

        # select points outside the AoI
        # TODO: shouldn't be the point to close the border removed here
        #       as well?
        arcpy.management.SelectLayerByLocation(
            points_layer, "WITHIN", aoi_polygon, "", "NEW_SELECTION", "INVERT"
        )
        pointsOID = arcpy.Describe(dataset).OIDFieldName
        outsideList = []
        # get their IDs
        with arcpy.da.SearchCursor(points_layer, [pointsOID]) as table:
            for row in table:
                outsideList.append(row[0])

        if outsideList:
            # report them to the user
            Logger.info(
                "\t{} record points outside of "
                "the area of interest ({}: {})".format(
                    len(outsideList), pointsOID, ",".join(map(str, outsideList))
                )
            )

        return points_clipped

    def _rst2np(self, raster):
        """See base method for description.
        """
        arr = arcpy.RasterToNumPyArray(
            raster, nodata_to_value=GridGlobals.NoDataValue
        )
        self._check_rst2np(arr)

        return arr

    def _update_grid_globals(self, reference, reference_cellsize):
        """See base method for description.
        """
        desc = arcpy.Describe(reference)
        desc_cellsize = arcpy.Describe(reference_cellsize)

        GridGlobals.r = desc.height
        GridGlobals.c = desc.width

        # lower left corner coordinates
        GridGlobals.set_llcorner((desc.Extent.XMin, desc.Extent.YMin))
        GridGlobals.set_size((desc_cellsize.MeanCellWidth, desc_cellsize.MeanCellHeight))
        inp = arcpy.Describe(self._input_params['elevation'])
        self._check_resolution_consistency(
            inp.meanCellWidth, inp.meanCellHeight
        )

        # set arcpy environment (needed for rasterization)
        arcpy.env.extent = desc.Extent
        arcpy.env.snapRaster = reference_cellsize

    def _compute_effect_cont(self, dem, asp):
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

        effect_cont = arcpy.sa.Times(times1, GridGlobals.dx)
        effect_cont.save(self.storage.output_filepath('effect_cont'))

        return self._rst2np(effect_cont)

    def _prepare_soilveg(self, soil, soil_type_fieldname, vegetation,
                         vegetation_type_fieldname, aoi_polygon,
                         soil_vegetation_table):
        """See base method for description.
        """
        # check if the soil_type_fieldname and vegetation_type_fieldname field
        # names are equal and deal with it if not
        if soil_type_fieldname == vegetation_type_fieldname:
            veg_fieldname = self.fieldnames['veg_type_fieldname']
            Logger.info(
                "The vegetation type attribute field name ('{}') is equal to "
                "the soil type attribute field name. Vegetation type attribute "
                "will be renamed to '{}'.".format(
                    vegetation_type_fieldname, veg_fieldname
                )
            )

            # arcpy.management.AlterField(vegetation,vegetation_type_fieldname, veg_fieldname) # - does not work correctly, better to add field -> copy values -> delete field
            # add new field
            arcpy.management.AddField(vegetation, veg_fieldname, "TEXT")
            # copy the values and delete the old field
            with arcpy.da.UpdateCursor(vegetation, [vegetation_type_fieldname, veg_fieldname]) as table:
                for row in table:
                    row[0] = row[1]
                    table.updateRow(row)
            arcpy.management.DeleteField(vegetation, vegetation_type_fieldname)
        else:
            veg_fieldname = vegetation_type_fieldname

        # create the geometric intersection of soil and vegetation layers
        soilveg_aoi_path = self.storage.output_filepath("soilveg_aoi")
        arcpy.analysis.Intersect(
            [soil, vegetation, aoi_polygon], soilveg_aoi_path, "NO_FID"
        )

        soilveg_code = self._input_params['table_soil_vegetation_fieldname']
        if soilveg_code in arcpy.ListFields(soilveg_aoi_path):
            arcpy.management.DeleteField(soilveg_aoi_path, soilveg_code)
            Logger.info(
                "'{}' attribute field already in the table and will be "
                "replaced.".format(soilveg_code)
            )

        arcpy.management.AddField(soilveg_aoi_path, soilveg_code, "TEXT")

        # calculate "soil_veg" values
        # = (soil_type_fieldname + vegetation_type_fieldname)
        with arcpy.da.UpdateCursor(soilveg_aoi_path, [soil_type_fieldname, veg_fieldname, soilveg_code]) as table:
            for row in table:
                row[2] = row[0] + row[1]
                table.updateRow(row)

        # join soil and vegetation model parameters from input table
        arcpy.management.JoinField(
            soilveg_aoi_path, soilveg_code,
            soil_vegetation_table,
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
                            "(field '{}': empty value found in row {})".format(
                                self.sfield[i], row_id
                            )
                        )

        # generate numpy array of soil and vegetation attributes
        for field in self.soilveg_fields.keys():
            output = self.storage.output_filepath(
                "soilveg_aoi_{}".format(field)
            )
            aoi_mask = self.storage.output_filepath('aoi_mask')
            with arcpy.EnvManager(nodata=GridGlobals.NoDataValue, cellSize=aoi_mask, cellAlignment=aoi_mask, snapRaster=aoi_mask):
                arcpy.conversion.PolygonToRaster(
                    soilveg_aoi_path, field, output, cellsize=GridGlobals.dy
                )
            self.soilveg_fields[field] = self._rst2np(output)
            self._check_soilveg_dim(field)

    def _get_points_location(self, points_layer, points_fieldname):
        """See base method for description.
        """
        points_array = None
        if points_layer:
            # get number of points
            count = int(arcpy.management.GetCount(points_layer).getOutput(0))
            if count > 0:
                points_array = np.zeros([int(count), 5], float)
                # get the points geometry and IDs into array
                desc = arcpy.Describe(points_layer)
                with arcpy.da.SearchCursor(points_layer, [points_fieldname, desc.ShapeFieldName]) as table:
                    i = 0
                    for row in table:
                        fid = row[0]
                        x, y = row[1]
                        rc = self._get_point_dem_coords(x, y)
                        if rc:
                            self._update_points_array(
                                points_array, i, fid, rc[0], rc[1], x, y
                            )
                        else:
                            Logger.info(
                                "Point FID = {} is at the edge of the raster. "
                                "This point will not be included in "
                                "results.".format(fid))
                        i += 1
            else:
                raise DataPreparationInvalidInput(
                    "None of the record points lays within the modeled area."
                )

        return points_array

    def _stream_clip(self, stream, aoi_polygon):
        """See base method for description.
        """
        #  AoI slighty smaller due to start/end elevation extraction
        aoi_buffer = arcpy.analysis.Buffer(
            aoi_polygon,
            self.storage.output_filepath('aoi_buffer'),
            -GridGlobals.dx / 3,
            "FULL", "ROUND",
        )

        stream_aoi = self.storage.output_filepath('streams_aoi')
        arcpy.analysis.Clip(stream, aoi_buffer, stream_aoi)

        # make sure that no of the stream properties fields are in the stream
        # feature class
        drop_fields = self._stream_check_fields(stream_aoi)
        for f in drop_fields:
            arcpy.management.DeleteField(stream_aoi, f)

        return stream_aoi

    def _stream_direction(self, stream, dem_aoi):
        """See base method for description.
        """
        segment_id_fieldname = self.fieldnames['stream_segment_id']
        start_elev_fieldname = self.fieldnames['stream_segment_start_elevation']
        end_elev_fieldname = self.fieldnames['stream_segment_end_elevation']
        inclination_fieldname = self.fieldnames['stream_segment_inclination']
        next_down_id_fieldname = self.fieldnames['stream_segment_next_down_id']
        segment_length_fieldname = self.fieldnames['stream_segment_length']

        # segments properties
        segment_props = {}

        # add the streamID for later use, get the 2D length of the stream
        # segments
        length_fieldname = arcpy.Describe(stream).lengthFieldName
        arcpy.management.AddField(stream, segment_id_fieldname, "SHORT")
        segment_id = 1
        with arcpy.da.UpdateCursor(stream, [segment_id_fieldname, length_fieldname]) as segments:
            for row in segments:
                row[0] = segment_id
                segments.updateRow(row)
                segment_props.update({segment_id: {'length': row[1]}})
                segment_id += 1

        # extract elevation for the stream segment vertices
        dem_array = self._rst2np(dem_aoi)

        shape_fieldname = arcpy.Describe(stream).shapeFieldName + "@"
        with arcpy.da.SearchCursor(stream, [shape_fieldname, segment_id_fieldname]) as segments:
            for row in segments:
                startpt = row[0].firstPoint
                r, c = self._get_point_dem_coords(startpt.X, startpt.Y)
                startpt.Z = float(dem_array[r][c])
                endpt = row[0].lastPoint
                r, c = self._get_point_dem_coords(endpt.X, endpt.Y)
                endpt.Z = float(dem_array[r][c])

                # negative elevation change is the correct direction for
                # stream segments
                elev_change = endpt.Z - startpt.Z

                if elev_change == 0:
                    raise DataPreparationError(
                        'Stream segment {}: {} has zero slope'.format(
                            segment_id_fieldname, row[1]
                        )
                    )
                elif elev_change < 0:
                    segment_props.get(row[1]).update({'start_point': startpt})
                    segment_props.get(row[1]).update({'end_point': endpt})
                else:
                    segment_props.get(row[1]).update({'start_point': endpt})
                    segment_props.get(row[1]).update({'end_point': startpt})

                inclination = elev_change/segment_props.get(row[1]).get(
                    'length'
                )
                segment_props.get(row[1]).update({'inclination': inclination})

        # add new fields to the stream segments feature class
        arcpy.management.AddField(stream, segment_id_fieldname, "SHORT")
        arcpy.management.AddField(stream, start_elev_fieldname, "DOUBLE")
        arcpy.management.AddField(stream, end_elev_fieldname, "DOUBLE")
        arcpy.management.AddField(stream, inclination_fieldname, "DOUBLE")
        arcpy.management.AddField(stream, next_down_id_fieldname, "SHORT")
        arcpy.management.AddField(stream, segment_length_fieldname, "DOUBLE")

        xy_tolerance = 0.01
        # don't know why the arcpy.env.XYtolerance does not work
        # (otherwise would use the arcpy.Point.equals() method)
        with arcpy.da.UpdateCursor(stream, [segment_id_fieldname, shape_fieldname, start_elev_fieldname,
                                            end_elev_fieldname, inclination_fieldname, next_down_id_fieldname,
                                            segment_length_fieldname, length_fieldname]) as table:
            for row in table:
                segment_props_row0 = segment_props.get(row[0])
                segment_inclination = segment_props_row0.get('inclination')
                row[1] = row[1] if segment_inclination < 0 else self._reverse_line_direction(row[1])
                row[2] = segment_props_row0.get('start_point').Z
                row[3] = segment_props_row0.get('end_point').Z
                row[4] = abs(segment_inclination)
                row[6] = segment_props_row0.get("length")

                # find the next down segment by comparing the points distance
                next_down_id = Globals.streamsNextDownIdNoSegment
                matched = 0
                for segment_id in segment_props.keys():
                    dist = pow(
                        pow(row[1].lastPoint.X-segment_props.get(segment_id).get('start_point').X, 2) + pow(row[1].lastPoint.Y-segment_props.get(segment_id).get('start_point').Y, 2),
                        0.5
                    )
                    if dist < xy_tolerance:
                        next_down_id = segment_id
                        matched += 1
                if matched > 1:
                    row[5] = None
                    raise DataPreparationError(
                        'Incorrect stream network topology downstream segment '
                        'streamID: {}. The network can not bifurcate.'.format(
                            row[0]
                        )
                    )
                else:
                    row[5] = next_down_id
                table.updateRow(row)

    @staticmethod
    def _reverse_line_direction(line):
        """Flip the order of points if a line to change its direction.

        If the geometry is multipart the parts are dissolved into single part
        line.

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
        stream_seg = self.storage.output_filepath('streams_seg')
        arcpy.conversion.PolylineToRaster(
            stream, self.fieldnames['stream_segment_id'], stream_seg,
            "MAXIMUM_LENGTH", cellsize=GridGlobals.dx
        )

        mat_stream_seg = self._rst2np(stream_seg)
        # ML: is no_of_streams needed (-> mat_stream_seg.max())
        self._get_mat_stream_seg(mat_stream_seg)

        return mat_stream_seg.astype('int16')

    def _stream_shape(self, streams, channel_shape_code,
                      channel_properties_table):
        """See base method for description.
        """
        if channel_shape_code not in self._get_field_names(streams):
            raise DataPreparationError(
                "Error joining channel shape properties to stream network "
                "segments!\nCheck fields names in stream network feature "
                "class. Missing field is: '{}'".format(
                    self._input_params['streams_channel_type_fieldname']
                )
            )

        arcpy.management.JoinField(
            streams, channel_shape_code, channel_properties_table,
            channel_shape_code, self.stream_shape_fields
        )

        stream_attr = self._get_streams_attr_()
        fields = list(stream_attr.keys())
        with arcpy.da.SearchCursor(streams, fields) as cursor:
            try:
                for row in cursor:
                    for i in range(len(row)):
                        if row[i] in (" ", None):
                            raise DataPreparationError(
                                "Empty value in {} ({}) found.".format(
                                    self._input_params[
                                        "channel_properties_table"
                                    ],
                                    fields[i])
                            )
                        stream_attr[fields[i]].append(row[i])

            except RuntimeError as e:
                raise DataPreparationError(
                        "Error: {}\n" 
                        "Check fields names in {}. "
                        "Proper columns codes are: {}".format(
                            e, self._input_params["channel_properties_table"],
                            self.stream_shape_fields
                        )
                )

        return self._decode_stream_attr(stream_attr)

    def _get_field_values(self, table, field):
        """See base method for description.
        """
        with arcpy.da.SearchCursor(table, [field]) as cursor:
            values = []
            for row in cursor:
                values.append(row[0])
        return values

    def _check_input_data(self):
        """See base method for description.
        """
        self._check_input_data_()

    def _get_field_names(self, ds):
        """See base method for description.
        """
        return [field.name for field in arcpy.ListFields(ds)]
