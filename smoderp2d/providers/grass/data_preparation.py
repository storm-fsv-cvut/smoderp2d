import numpy as np
import sqlite3
import tempfile
from subprocess import PIPE

from smoderp2d.core.general import GridGlobals, Globals

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput, \
    DataPreparationError, DataPreparationNoIntersection
from smoderp2d.providers.base.data_preparation import PrepareDataGISBase

from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.vector.table import Table, get_path
from grass.pygrass.raster import RasterRow, raster2numpy
from grass.pygrass.gis import Mapset
from grass.pygrass.gis.region import Region
from grass.exceptions import CalledModuleError, OpenError


class PrepareData(PrepareDataGISBase):

    def __init__(self, options, writer):
        # defile input parameters
        self._set_input_params(options)
        # TODO: output directory not defined by GRASS (data are written into
        # current mapset by default)
        self._input_params['output'] = None
        # os.path.join(Location().path(), "output")

        super(PrepareData, self).__init__(writer)

        # install r.hydrodem if not available
        install_ext = False
        ext = Module('g.extension', flags='a', stdout_=PIPE)
        list_ext = ext.outputs.stdout.splitlines()
        if 'r.hydrodem' not in list_ext:
            install_ext = True
        else:
            # try to run the module
            try:
                Module("r.hydrodem", run_=False)
            except Exception:
                install_ext = True
        if install_ext:
            Logger.info("Installing r.hydrodem extension...")
            Module('g.extension', extension='r.hydrodem')

    def __del__(self):
        # remove mask
        try:
            Module('r.mask', flags='r')
        except CalledModuleError:
            pass  # mask not exists

    @staticmethod
    def __qualified_name(name, mtype='vector'):
        """Get qualified map name as dict used by Vector class.

        :param name: map name
        :param mtype: TODO
        """
        if '@' in name:
            map_name, mapset = name.split('@', 1)
        else:
            map_name = name
            mapset = Mapset().name

        qualified_name = {'name': map_name}

        if mtype == 'vector':
            qualified_name.update({'mapset': mapset})
        elif mtype == 'table':
            path = '$GISDBASE/$LOCATION_NAME/{}/sqlite/sqlite.db'.format(mapset)
            qualified_name.update(
                {'connection': sqlite3.connect(get_path(path))}
            )
        else:
            raise DataPreparationError(
                "Unexpected mtype {} in __qualified_name".format(mtype)
            )

        return qualified_name

    def __remove_temp_data(self, kwargs):
        if kwargs['type'] != 'table':
            self._run_grass_module('g.remove', flags="f", **kwargs)
        else:
            self._run_grass_module('db.droptable', table=kwargs['name'])

    def _create_AoI_outline(self, elevation, soil, vegetation):
        """See base method for description."""
        self._run_grass_module('g.region', raster=elevation)
        dem_slope_mask_path = self.storage.output_filepath('dem_slope_mask')
        self._run_grass_module(
            'r.recode', input=elevation, output=dem_slope_mask_path+'1',
            rules="-", stdin_="-100000:100000:1"
        )
        # the slope raster extent will be used in further
        # intersections as it is always smaller than the DEM extent
        # ...
        # r.grow requires computation region to be larger
        with RasterRow(elevation) as rmap:
            nsres = rmap.info.nsres
            ewres = rmap.info.ewres
        self._run_grass_module(
            'g.region', n='n+{}'.format(nsres), s='s-{}'.format(nsres),
            e='e+{}'.format(ewres), w='w-{}'.format(ewres))
        self._run_grass_module(
            'r.grow', input=dem_slope_mask_path+'1',
            output=dem_slope_mask_path, radius=-1.01, metric="maximum"
        )
        self.__remove_temp_data(
            {'name': dem_slope_mask_path+'1', 'type': 'raster'}
        )

        dem_polygon = self.storage.output_filepath('dem_polygon')
        self._run_grass_module(
            'r.to.vect', input=dem_slope_mask_path, output=dem_polygon,
            flags="v", type="area"
        )
        aoi = self.storage.output_filepath('aoi')
        self._run_grass_module(
            'v.clip', input=soil, clip=dem_polygon, output=aoi+'1'
        )
        self._run_grass_module(
            'v.overlay', ainput=aoi+'1', binput=vegetation, operator='and',
            output=aoi
        )
        self.__remove_temp_data({'name': aoi+'1', 'type': 'vector'})

        aoi_polygon = self.storage.output_filepath('aoi_polygon')
        self._run_grass_module(
            'v.db.addcolumn', map=aoi, columns="dissolve int"
        )
        self._run_grass_module(
            'v.db.update', map=aoi, column='dissolve', value=1
        )
        self._run_grass_module(
            'v.dissolve', input=aoi, column='dissolve', output=aoi_polygon
        )

        with VectorTopo(aoi_polygon) as vmap:
            count = vmap.number_of('areas')
        if count == 0:
            raise DataPreparationNoIntersection()

        aoi_mask = self.storage.output_filepath('aoi_mask')
        self._run_grass_module('g.region', vector=aoi_polygon, align=elevation)
        self._run_grass_module(
            'v.to.rast', input=aoi_polygon, type='area', use='cat',
            output=aoi_mask+'1'
        )

        # perform aoi_mask postprocessing - remove no-data cells on the edges
        self._run_grass_module('g.region', zoom=aoi_mask+'1')
        self._run_grass_module(
            'r.mapcalc', expression=f'{aoi_mask} = {aoi_mask}1'
        )
        self._run_grass_module(
            'r.to.vect', input=aoi_mask, output=aoi_polygon,
            flags="v", type="area"
        )
        self.__remove_temp_data({'name': aoi_mask+'1', 'type': 'raster'})

        return aoi_polygon, aoi_mask

    def _create_DEM_derivatives(self, dem):
        """See base method for description."""
        self._run_grass_module('g.region', raster=dem)
        dem_filled = self.storage.output_filepath('dem_filled')
        dem_flowdir = self.storage.output_filepath('dem_flowdir')
        # calculate the depressionless DEM
        self._run_grass_module(
            'r.hydrodem', flags='f', input=dem, output=dem_filled
        )

        # calculate the flow direction
        # calculate flow accumulation
        dem_flowacc = self.storage.output_filepath('dem_flowacc')
        self._run_grass_module(
            'r.watershed', flags='as', elevation=dem_filled,
            drainage=dem_flowdir+'1', accumulation=dem_flowacc
        )
        # recalculate flow dir to ArcGIS notation
        # https://idea.isnew.info/how-to-import-arcgis-flow-direction-into-grass-gis.html
        # ML: flowdir is slightly different compared to ArcGIS
        # ML: flowacc is slightly different compared to ArcGIS
        reclass = """
-1 1 = 128
-2 2 = 64
-3 3 = 32
-4 4 = 16
-5 5 = 8
-6 6 = 4
-7 7 = 2
-8 8 = 1
"""
        self._run_grass_module(
            'r.reclass', input=dem_flowdir+'1', output=dem_flowdir,
            rules='-', stdin_=reclass
        )
        self.__remove_temp_data(
            {'name': '{r}1'.format(r=dem_flowdir), 'type': 'raster'}
        )

        # calculate slope
        dem_slope = self.storage.output_filepath('dem_slope')
        dem_aspect = self.storage.output_filepath('dem_aspect')
        self._run_grass_module(
            'r.slope.aspect', elevation=dem, format='percent',
            slope=dem_slope, aspect=dem_aspect
        )

        return dem_filled, dem_flowdir, dem_flowacc, dem_slope, dem_aspect

    def _clip_raster_layer(self, dataset, aoi_mask, name):
        """See base method for description."""
        output = self.storage.output_filepath(name)
        self._run_grass_module('g.region', raster=aoi_mask)
        self._run_grass_module(
            'r.mapcalc',
            expression='{o} = if(isnull({m}), null(), {i})'.format(
                o=output, m=aoi_mask, i=dataset
            )
        )

        return output

    def _clip_record_points(self, dataset, aoi_polygon, name):
        """See base method for description."""
        # select points inside the AIO
        points_clipped = self.storage.output_filepath(name)
        self._run_grass_module(
            'v.select', ainput=dataset, binput=aoi_polygon,
            operator='within', output=points_clipped
        )
        # if no points selected v.select doesn't create any output
        if points_clipped not in Mapset().glist('vector'):
            self._run_grass_module(
                'v.edit', map=points_clipped, tool='create'
            )

        # select points outside the AoI
        self._run_grass_module(
            'v.select', flags='r', ainput=dataset, binput=aoi_polygon,
            operator='within', output=points_clipped+'1'
        )
        outside_list = []
        try:
            # get their IDs
            with Vector(points_clipped + '1') as vmap:
                vmap.table.filters.select(self.storage.primary_key)
                for row in vmap.table:
                    outside_list.append(row[0])
            self.__remove_temp_data(
                {'name': points_clipped+'1', 'type': 'vector'}
            )

            # report them to the user
            Logger.info(
                "\t{} record points outside of the area of interest "
                "({}: {})".format(
                    len(outside_list), "FID", ",".join(map(str, outside_list))
                )
            )
        except OpenError:
            # only created if there is at least one point out of AOI
            pass

        return points_clipped

    def _rst2np(self, raster):
        """See base method for description."""
        # raster is read from current computation region
        # g.region cannot be called here,
        # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
        region = Region()
        region.from_rast(raster)
        region.set_raster_region()
        array = raster2numpy(raster)
        if np.issubdtype(array.dtype, np.integer):
            array[array == -2**31] = GridGlobals.NoDataValue
        else:
            np.nan_to_num(array, copy=False, nan=GridGlobals.NoDataValue)

        self._check_rst2np(array)

        return array

    def _update_grid_globals(self, reference, reference_cellsize):
        """See base method for description.
        """
        # lower left corner coordinates
        with RasterRow(reference) as data:
            GridGlobals.r = data.info.rows
            GridGlobals.c = data.info.cols
            GridGlobals.set_llcorner((data.info.west, data.info.south))
            GridGlobals.set_size((data.info.ewres, data.info.nsres))

            self._check_resolution_consistency(data.info.ewres, data.info.nsres)

    def _compute_effect_cont(self, dem, asp):
        """See base method for description."""
        # conversion to radians not needed, GRASS's sin() assumes degrees
        ratio_cell = self.storage.output_filepath('ratio_cell')
        self._run_grass_module(
            'r.mapcalc',
            expression='{o} = abs(sin({a})) + abs(cos({a}))'.format(
                o=ratio_cell, a=asp
            )
        )

        effect_cont = self.storage.output_filepath('effect_cont')
        self._run_grass_module(
            'r.mapcalc',
            expression='{} = {} * {}'.format(
                effect_cont, ratio_cell, GridGlobals.dx
            )
        )

        return self._rst2np(effect_cont)

    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_polygon, table_soil_vegetation):
        """See base method for description."""
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
            self._run_grass_module(
                'v.db.renamecolumn', map=vegetation,
                column=[vegetation_type, veg_fieldname]
            )
        else:
            veg_fieldname = vegetation_type

        # create the geometric intersection of soil and vegetation layers
        soilveg_aoi = self.storage.output_filepath("soilveg_aoi")
        soil_aoi = self.__qualified_name(soil)['name']+'1'
        self._run_grass_module(
            'v.clip', input=soil, clip=aoi_polygon, output=soil_aoi
        )
        self._run_grass_module(
            'v.overlay', ainput=soil_aoi, binput=vegetation, operator='and',
            output=soilveg_aoi
        )
        self.__remove_temp_data({'name': soil_aoi, 'type': 'vector'})

        soilveg_code = self._input_params['table_soil_vegetation_fieldname']
        fields = self._get_field_names(soilveg_aoi)
        if soilveg_code in fields:
            self._run_grass_module(
                'v.db.dropcolumn', map=soilveg_aoi, columns=[soilveg_code]
            )
            Logger.info(
                "'{}' attribute field already in the table and will be "
                "replaced.".format(soilveg_code)
            )
        self._run_grass_module(
            'v.db.addcolumn', map=soilveg_aoi,
            columns=["{} varchar(15)".format(soilveg_code)]
        )

        # calculate "soil_veg" values (soil_type + vegetation_type)
        self._run_grass_module(
            'v.db.update', map=soilveg_aoi, column=soilveg_code,
            query_column='a_{} || b_{}'.format(soil_type, vegetation_type)
        )

        # join soil and vegetation model parameters from input table
        # v.db.join doesn't support to access tables from other mapsets
        soilveg_table = self.__qualified_name(
            table_soil_vegetation, mtype='table'
        )['name']
        self._run_grass_module(
            'db.copy',
            from_table=soilveg_table,
            to_table=soilveg_table,
            from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db'
        )
        self._run_grass_module(
            'v.db.join', map=soilveg_aoi, column=soilveg_code,
            other_table=soilveg_table, other_column=soilveg_code,
            subset_columns=list(self.soilveg_fields.keys())
        )
        self.__remove_temp_data({'name': soilveg_table, 'type': 'table'})

        # check for empty values
        with Vector(soilveg_aoi) as vmap:
            soilveg_fields = list(self.soilveg_fields.keys())
            vmap.table.filters.select(*soilveg_fields)
            for row in vmap.table:
                for i in range(len(row)):
                    if row[i] in ("", " ", None):
                        raise DataPreparationInvalidInput(
                            "Values in soilveg table are not correct "
                            "(field '{}': empty value found in row {}). It is"
                            "recommended to check if the {} code is present in"
                            " soil and landuse parameter table".format(
                                soilveg_fields[i], i, soilveg_code
                            )
                        )

        # generate numpy array of soil and vegetation attributes
        for field in self.soilveg_fields.keys():
            output = self.storage.output_filepath(
                "soilveg_aoi_{}".format(field)
            )
            self._run_grass_module(
                'v.to.rast', input=soilveg_aoi, type='area', use='attr',
                attribute_column=field, output=output
            )
            self.soilveg_fields[field] = self._rst2np(output)
            self._check_soilveg_dim(field)

    def _get_points_location(self, points_layer, points_fieldname):
        """See base method for description."""
        points_array = None
        if points_layer:
            # get number of points
            points_map = self.__qualified_name(points_layer)
            with VectorTopo(**points_map) as vmap:
                count = vmap.number_of('points')
            if count > 0:
                points_array = np.zeros([int(count), 5], float)
                # get the points geometry and IDs into array
                with VectorTopo(**points_map) as vmap:
                    i = 0
                    for p in vmap:
                        fid = p.attrs[points_fieldname]
                        x, y = p.x, p.y
                        rc = self._get_point_dem_coords(x, y)
                        if rc:
                            self._update_points_array(
                                points_array, i, fid, rc[0], rc[1], x, y
                            )
                        else:
                            Logger.info(
                                f"Point FID = {fid} is at the edge of the "
                                f"raster. This point will not be included in "
                                f"results."
                            )
                        i += 1
            else:
                raise DataPreparationInvalidInput(
                    "None of the record points lays within the modeled area."
                )

        return points_array

    def _stream_clip(self, stream, aoi_polygon):
        """See base method for description."""
        # AoI slighty smaller due to start/end elevation extraction
        aoi_buffer = self.storage.output_filepath('aoi_buffer')
        self._run_grass_module(
            'v.buffer', input=aoi_polygon, output='aoi_buffer',
            distance=-GridGlobals.dx / 3
        )

        stream_aoi = self.storage.output_filepath('streams_aoi')
        self._run_grass_module(
            'v.clip', input=stream, clip=aoi_buffer, output='streams_aoi_unclean'
        )
        # clean topology
        # (necessary for stream connection snapped in lines instead of points)
        self._run_grass_module(
            'v.clean', input='streams_aoi_unclean', tool='break',
            output=stream_aoi
        )
        self.__remove_temp_data(
            {'name': 'streams_aoi_unclean', 'type': 'vector'}
        )

        drop_fields = self._stream_check_fields(stream_aoi)
        if drop_fields:
            self._run_grass_module(
                'v.db.dropcolumn', map=stream_aoi, columns=drop_fields
            )

        return stream_aoi

    def _stream_direction(self, stream, dem):
        """See base method for description."""
        segment_id_fieldname = self.fieldnames['stream_segment_id']
        start_elev_fieldname = self.fieldnames[
            'stream_segment_start_elevation'
        ]
        end_elev_fieldname = self.fieldnames['stream_segment_end_elevation']
        inclination_fieldname = self.fieldnames['stream_segment_inclination']
        next_down_fieldname = self.fieldnames['stream_segment_next_down_id']
        segment_length_fieldname = self.fieldnames['stream_segment_length']

        # segments properties
        segment_props = {}

        # add the streamID for later use, get the 2D length of the stream
        # segments
        self._run_grass_module(
            'v.db.addcolumn', map=stream,
            columns=['{} integer'.format(segment_id_fieldname)]
        )
        with VectorTopo(stream) as vmap:
            segment_id = 1
            for f in vmap:
                f.attrs[segment_id_fieldname] = segment_id
                segment_props.update({segment_id: {'length': f.length()}})
                segment_id += 1
            vmap.table.conn.commit()

        # extract elevation for the stream segment vertices
        dem_array = self._rst2np(dem)

        to_reverse = []
        with Vector(stream) as vmap:
            for seg in vmap:
                startpt = seg[0]
                r, c = self._get_point_dem_coords(startpt.x, startpt.y)
                startpt.z = float(dem_array[r][c])
                endpt = seg[-1]
                r, c = self._get_point_dem_coords(endpt.x, endpt.y)
                endpt.z = float(dem_array[r][c])

                # negative elevation change is the correct direction for stream
                # segments
                elev_change = endpt.z - startpt.z

                segment_id = seg.attrs[segment_id_fieldname]
                if elev_change == 0:
                    raise DataPreparationError(
                        'Stream segment {}: {} [[{}, {}], [{}, {}]] has zero '
                        'slope'.format(
                            segment_id_fieldname, segment_id, startpt.x,
                            startpt.y, endpt.x, endpt.y
                        )
                    )
                elif elev_change < 0:
                    segment_props.get(segment_id).update(
                        {'start_point': startpt}
                    )
                    segment_props.get(segment_id).update({'end_point': endpt})
                else:
                    to_reverse.append(str(segment_id))
                    segment_props.get(segment_id).update({'start_point': endpt})
                    segment_props.get(segment_id).update({'end_point': startpt})

                inclination = elev_change/segment_props.get(segment_id).get(
                    'length'
                )
                segment_props.get(segment_id).update(
                    {'inclination': inclination}
                )

        # add new fields to the stream segments feature class
        self._run_grass_module(
            'v.db.addcolumn',
            map=stream,
            columns=[
                '{} integer'.format(segment_id_fieldname),
                '{} double precision'.format(start_elev_fieldname),
                '{} double precision'.format(end_elev_fieldname),
                '{} double precision'.format(inclination_fieldname),
                '{} integer'.format(next_down_fieldname),
                '{} double precision'.format(segment_length_fieldname)
            ]
        )

        self._run_grass_module(
            'v.edit',
            map=stream,
            tool='flip',
            where='{} in ({})'.format(
                segment_id_fieldname, ','.join(to_reverse)
            )
        )

        with VectorTopo(stream) as vmap:
            for seg in vmap:
                segment_id = seg.attrs[segment_id_fieldname]
                segment_inclination = segment_props.get(segment_id).get(
                    "inclination"
                )
                seg.attrs[start_elev_fieldname] = segment_props.get(
                    segment_id
                ).get("start_point").z
                seg.attrs[end_elev_fieldname] = segment_props.get(
                    segment_id
                ).get("end_point").z
                seg.attrs[inclination_fieldname] = abs(segment_inclination)
                seg.attrs[segment_length_fieldname] = segment_props.get(
                    segment_id
                ).get("length")

                # find the next down segment by comparing the points distance
                _, end = seg.nodes()
                seg.attrs[next_down_fieldname] = Globals.streamsNextDownIdNoSegment
                for start_seg in end.lines():
                    if start_seg.id != seg.id and start_seg[0] == seg[-1]:
                        # start_seg[0] == seg[-1] -> check only outflowing
                        # streams, not inflowing
                        if seg.attrs[next_down_fieldname] != Globals.streamsNextDownIdNoSegment:
                            raise DataPreparationError(
                                'Incorrect stream network topology downstream '
                                'segment streamID: {}. The network can not '
                                'bifurcate (at point [{}, {}]).'.format(
                                    segment_id, seg[-1].x, seg[-1].y
                                )
                            )
                        seg.attrs[next_down_fieldname] = vmap[
                            start_seg.id
                        ].attrs[segment_id_fieldname]

            vmap.table.conn.commit()

        # stream layer modified, must be exported explicitly
        self._export_data(stream, 'vector')

    def _stream_reach(self, stream):
        """See base method for description."""
        self._run_grass_module(
            'g.region', s=GridGlobals.yllcorner, w=GridGlobals.xllcorner,
            n=GridGlobals.yllcorner+(GridGlobals.r * GridGlobals.dy),
            e=GridGlobals.xllcorner+(GridGlobals.c * GridGlobals.dx),
            ewres=GridGlobals.dx, nsres=GridGlobals.dy
        )

        stream_seg = self.storage.output_filepath('streams_seg')
        self._run_grass_module(
            'v.to.rast', input=stream, type='line', use='attr',
            attribute_column=self.fieldnames['stream_segment_id'],
            output=stream_seg, flags='d'
        )

        mat_stream_seg = self._rst2np(stream_seg)
        # ML: is no_of_streams needed (-> mat_stream_seg.max())
        self._get_mat_stream_seg(mat_stream_seg)

        return mat_stream_seg.astype('int16')

    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        """See base method for description."""
        stream_shape_tab = self.__qualified_name(
            stream_shape_tab, mtype='table')['name']
        self._run_grass_module(
            'db.copy',
            from_table=stream_shape_tab,
            from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db',
            to_table=stream_shape_tab)
        self._run_grass_module(
            'v.db.join',
            map=stream, column=stream_shape_code, other_table=stream_shape_tab,
            other_column=stream_shape_code,
            subset_columns=self.stream_shape_fields
        )

        stream_attr = self._get_streams_attr_()
        with Vector(stream) as vmap:
            vmap.table.filters.select(*stream_attr.keys())
            for row in vmap.table:
                fields = list(stream_attr.keys())
                for i in range(len(row)):
                    if row[i] in (" ", None):
                        raise DataPreparationError(
                            "Empty value in {} ({}) found.".format(
                                self._input_params["channel_properties_table"],
                                fields[i]
                            )
                        )
                    stream_attr[fields[i]].append(row[i])

        return self._decode_stream_attr(stream_attr)

    def _get_field_values(self, table, field):
        """See base method for description.
        """
        try:
            values = []
            with Vector(**self.__qualified_name(table)) as vmap:
                vmap.table.filters.select(field)
                for row in vmap.table:
                    values.append(row[0])
        except OpenError as e:
            raise DataPreparationInvalidInput(e)

        return values

    def _check_input_data(self):
        """See base method for description."""
        self._check_input_data_()

        # overlapping polygons (soils)
        try:
            soil = self._input_params['soil']
            with VectorTopo(**self.__qualified_name(soil)) as fd:
                for area in fd.viter('areas'):
                    cats = list(area.cats().get_list())
                    if len(cats) > 1:
                        raise DataPreparationInvalidInput(
                            "Overlapping soil polygons detected"
                        )
        except OpenError as e:
            raise DataPreparationInvalidInput(e)

    def _get_field_names(self, ds):
        """See base method for description."""
        if ds in Mapset().glist(type='vector'):
            with Vector(**self.__qualified_name(ds)) as vmap:
                fields = vmap.table.columns.names()
        else:
            table = Table(
                **self.__qualified_name(ds, mtype='table')
            )
            fields = table.columns.names()

        return fields

    def _run_grass_module(self, *args, **kwargs):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                kwargs['stderr_'] = tmp
                tmp_fn = tmp.name
                m = Module(*args, **kwargs)
        except CalledModuleError as e:
            with open(tmp_fn) as fd:
                error_msg = fd.read()
            Logger.error(f"Data preparation failed:\n{e}\n{error_msg}")
            raise DataPreparationError(f"Data preparation failed: {error_msg}")

        if self._input_params['generate_temporary'] is False:
            return 0

        export_layers = PrepareDataGISBase.data_layers.keys()
        if m.name == 'r.mapcalc':
            map_name = m.inputs.expression.split('=')[0].strip()
            if map_name in export_layers:
                self._export_data(map_name, 'raster')
        else:
            for p in m.outputs.values():
                if p.typedesc in ('raster', 'vector') and p.value is not None:
                    map_name = p.value
                    if map_name in export_layers:
                        self._export_data(map_name, p.typedesc)

    def _export_data(self, map_name, mtype):
        """Export GRASS data.

        :param map_name: map name
        :param mtype: map type
        """
        if map_name not in Mapset().glist(mtype):
            # skip export if map doesn't exist
            return

        output_path = self.storage.output_filepath(map_name, full_path=True)
        if mtype == 'raster':
            self.storage.export_raster(
                map_name,
                output_path
            )
        elif mtype == 'vector':
            self.storage.export_vector(
                map_name,
                output_path
            )
        else:
            raise DataPreparationError(
                f"Unsupported data type for export: {mtype}"
            )
