# import os
import math
from subprocess import PIPE

import numpy as np
import sqlite3

from smoderp2d.core.general import GridGlobals

from smoderp2d.providers.grass.manage_fields import ManageFields

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput, \
    DataPreparationError, DataPreparationNoIntersection
from smoderp2d.providers.base.data_preparation import PrepareDataBase

from grass.script.core import tempfile
from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.vector.table import Table, get_path
from grass.pygrass.raster import RasterRow, raster2numpy
from grass.pygrass.gis import Region, Mapset
from grass.exceptions import CalledModuleError, OpenError

class PrepareData(PrepareDataBase, ManageFields):
    def __init__(self, options, writter):
        # defile input parameters
        self._set_input_params(options)
        # TODO: output directory not defined by GRASS (data are written into
        # current mapset by default)
        self._input_params['output'] = None # os.path.join(Location().path(), "output")

        super(PrepareData, self).__init__(writter)

    def __del__(self):
        # remove mask
        try:
            Module('r.mask',
                   flags='r'
            )
        except CalledModuleError:
            pass # mask not exists

    @staticmethod
    def __qualified_name(name, mtype='vector'):
        """Get qualified map name as dict used by Vector class.

        :param name: map name
        """
        if '@' in name:
            part1, part2 = name.split('@', 1)
            if mtype == 'vector': 
                return { 'name': part1, 'mapset': part2 }
            elif mtype == 'table':
                path = '$GISDBASE/$LOCATION_NAME/{}/sqlite/sqlite.db'.format(part2)
                return { 'name': part1, 'connection': sqlite3.connect(get_path(path)) }
            else:
                raise DataPreparationError("Unexpected mtype {} in __qualified_name".format(mtype))

        return { 'name': name }

    @staticmethod
    def __remove_temp_data(kwargs):
        if kwargs['type'] != 'table':
            Module('g.remove', flags="f", **kwargs)
        else:
            Module('db.droptable', table=kwargs['name'])

    def _create_AoI_outline(self, elevation, soil, vegetation):
        """See base method for description.
        """
        Module('g.region',
               raster=elevation)
        dem_slope_mask_path = self.storage.output_filepath('dem_slope_mask')
        Module('r.recode',
               input=elevation, output=dem_slope_mask_path+'1',
               rules="-", stdin_="-100000:100000:1")
        # r.grow requires computation region to be larger
        with RasterRow(elevation) as rmap:
            nsres = rmap.info.nsres
            ewres = rmap.info.ewres
        Module('g.region',
               n='n+{}'.format(nsres), s='s-{}'.format(nsres),
               e='e+{}'.format(ewres), w='w-{}'.format(ewres))
        Module('r.grow',
               input=dem_slope_mask_path+'1', output=dem_slope_mask_path,
               radius=-1.01, metric="maximum")
        self.__remove_temp_data({'name': dem_slope_mask_path+'1', 'type': 'raster'})
        
        dem_polygon = self.storage.output_filepath('dem_polygon')
        Module('r.to.vect',
               input=dem_slope_mask_path, output=dem_polygon,
               flags="v", type="area")
        aoi = self.storage.output_filepath('aoi')
        Module('v.clip',
               input=soil, clip=dem_polygon,
               output=aoi+'1')
        Module('v.overlay',
               ainput=aoi+'1', binput=vegetation,
               operator='and', output=aoi)
        self.__remove_temp_data({'name': aoi+'1', 'type': 'vector'})

        aoi_polygon = self.storage.output_filepath('aoi_polygon')
        Module('v.db.addcolumn',
               map=aoi, columns="dissolve int")
        Module('v.db.update',
               map=aoi, column='dissolve', value=1)
        Module('v.dissolve',
               input=aoi, column='dissolve', output=aoi_polygon)

        with VectorTopo(aoi_polygon) as vmap:
            count = vmap.number_of('areas')
        if count == 0:
            raise DataPreparationNoIntersection()

        return aoi_polygon

    def _create_DEM_derivatives(self, dem):
        """See base method for description.
        """
        Module('g.region',
               raster=dem)
        dem_filled = self.storage.output_filepath('dem_filled')
        dem_flowdir = self.storage.output_filepath('dem_flowdir')
        # calculate the depressionless DEM
        Module('r.fill.dir',
               input=dem, output=dem_filled,
               format='agnps',
               direction=dem_flowdir+'2')

        # calculate the flow direction
        # calculate flow accumulation        
        dem_flowacc = self.storage.output_filepath('dem_flowacc')
        Module('r.watershed',
               flags='as', elevation=dem,
               drainage=dem_flowdir+'1', accumulation=dem_flowacc)
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
        Module('r.reclass',
               input=dem_flowdir+'1', output=dem_flowdir,
               rules='-', stdin_=reclass)
        self.__remove_temp_data({'name': '{r}1,{r}2'.format(r=dem_flowdir), 'type': 'raster'})

        # calculate slope
        dem_slope = self.storage.output_filepath('dem_slope')
        dem_aspect = self.storage.output_filepath('dem_aspect')        
        Module('r.slope.aspect',
               elevation=dem_filled,
               format='percent', slope=dem_slope,
               aspect=dem_aspect)

        return dem_filled, dem_flowdir, dem_flowacc, dem_slope, dem_aspect

    
    def _clip_raster_layer(self, dataset, aoi_polygon, name):
        """See base method for description.
        """
        output = self.storage.output_filepath(name)
        if aoi_polygon not in Mapset().glist(type='raster'):
            Module('v.to.rast',
                   input=aoi_polygon, type='area', use='cat',
                   output=aoi_polygon)
        Module('r.mapcalc',
               expression='{o} = if(isnull({m}), null(), {i})'.format(
                   o=output, m=aoi_polygon, i=dataset))

        return output
    
    def _clip_record_points(self, dataset, aoi_polygon, name):
        """See base method for description.
        """
        # select points inside the AIO        
        points_clipped = self.storage.output_filepath(name)
        Module('v.select',
               ainput=dataset, binput=aoi_polygon,
               operator='within',
               output=points_clipped)

        # select points outside the AoI
        Module('v.select',
               flags='r',
               ainput=dataset, binput=aoi_polygon,
               operator='within',
               output=points_clipped+'1')
        outsideList = []
        # get their IDs
        with Vector(points_clipped+'1') as vmap:
            vmap.table.filters.select(self.storage.primary_key)
            for row in vmap.table:
                outsideList.append(row[0])
        self.__remove_temp_data({'name': points_clipped+'1', 'type': 'vector'})

        # report them to the user
        Logger.info("\t{} record points outside of the area of interest ({}: {})".format(
            len(outsideList), "FID", ",".join(map(str, outsideList)))
        )
                
        return points_clipped
 
    def _rst2np(self, raster):
        """See base method for description.
        """
        # raster is read from current computation region
        # g.region cannot be called here,
        # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
        region = Region()
        region.from_rast(raster)
        region.set_raster_region()
        return raster2numpy(raster)

    def _update_grid_globals(self, reference):
        """See base method for description.
        """
        # lower left corner coordinates        
        with RasterRow(reference) as data:
            # check data consistency
            # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
            if data.info.rows != GridGlobals.r or \
               data.info.cols != GridGlobals.c:
                raise DataPreparationError(
                    "Data inconsistency ({},{}) vs ({},{})".format(
                        data.info.rows, data.info.cols,
                        GridGlobals.r, GridGlobals.c)
                )
            GridGlobals.set_llcorner((data.info.west, data.info.south)) 
            GridGlobals.set_size((data.info.ewres, data.info.nsres))

    def _compute_efect_cont(self, dem, asp):
        """See base method for description.
        """
        # conversion to radias not needed, GRASS's sin() assumes degrees
        ratio_cell = self.storage.output_filepath('ratio_cell')
        Module('r.mapcalc',
               expression='{o} = abs(sin({a})) + abs(cos({a}))'.format(
                   o=ratio_cell, a=asp)
        )

        efect_cont = self.storage.output_filepath('efect_cont')        
        Module('r.mapcalc',
               expression='{} = {} * {}'.format(
                   efect_cont, ratio_cell, GridGlobals.dx
        ))

        return self._rst2np(efect_cont)

    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_polygon, table_soil_vegetation):
        """See base method for description.
        """
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
            Module('v.db.renamecolumn',
                   map=vegetation,
                   column=[vegetation_type, veg_fieldname]
            )
        else:
            veg_fieldname = vegetation_type

        # create the geometric intersection of soil and vegetation layers
        soilveg_aoi = self.storage.output_filepath("soilveg_aoi")
        soil_aoi = self.__qualified_name(soil)['name']+'1'
        Module('v.clip',
               input=soil, clip=aoi_polygon,
               output=soil_aoi)
        Module('v.overlay',
               ainput=soil_aoi,
               binput=vegetation,
               operator='and',
               output=soilveg_aoi)
        self.__remove_temp_data({'name': soil_aoi, 'type': 'vector'})

        soilveg_code = self._input_params['table_soil_vegetation_code']            
        with Vector(soilveg_aoi) as vmap:
            fields = vmap.table.columns.names()
        if soilveg_code in fields:
            Module('v.db.dropcolumn',
                   map=soilveg_aoi,
                   columns=[soilveg_code])
            Logger.info(
                "'{}' attribute field already in the table and will be replaced.".format(soilveg_code)
            )
        Module('v.db.addcolumn',
               map=soilveg_aoi,
               columns=["{} varchar(15)".format(soilveg_code)])

        # calculate "soil_veg" values (soil_type + vegetation_type)        
        Module('v.db.update',
               map=soilveg_aoi, column=soilveg_code,
               query_column='a_{} || b_{}'.format(
                   soil_type, vegetation_type))

        # join soil and vegetation model parameters from input table
        # v.db.join doesn't support to access tables from other mapsets
        soilveg_table = self.__qualified_name(table_soil_vegetation, mtype='table')['name']
        Module('db.copy',
               from_table=soilveg_table,
               to_table=soilveg_table,
               from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db'
        )        
        Module('v.db.join',
               map=soilveg_aoi, column=soilveg_code,
               other_table=soilveg_table,
               other_column=soilveg_code,
               subset_columns=list(self.soilveg_fields.keys()))
        self.__remove_temp_data({'name': soilveg_table, 'type': 'table'})
        
        # check for empty values
        with Vector(soilveg_aoi) as vmap:
            vmap.table.filters.select(*list(self.soilveg_fields.keys()))
            for row in vmap.table:
                for i in range(len(row)):
                    if row[i] in ("", " ", None):
                        raise DataPreparationInvalidInput(
                            "Values in soilveg table are not correct "
                            "(field '{}': empty value found in row {})".format(self.sfield[i], row_id)
                        )

        # generate numpy array of soil and vegetation attributes
        for field in self.soilveg_fields.keys():
            output = self.storage.output_filepath("soilveg_aoi_{}".format(field))
            Module('v.to.rast',
                   input=soilveg_aoi, type='area',
                   use='attr', attribute_column=field,
                   output=output)
            self.soilveg_fields[field] = self._rst2np(output)            
            self._check_soilveg_dim(field)

    def _get_array_points(self):
        """See base method for description.
        """
        array_points = None
        points_layer = self._input_params['points']
        if points_layer:
            points_map = self.__qualified_name(points_layer)
            # get number of points
            with VectorTopo(**points_map) as vmap:
                count = vmap.number_of('points')
            if count > 0:
                # empty array
                array_points = np.zeros([count, 5], float)

                # get the points geometry and IDs into array
                with Vector(**points_map) as vmap:
                    i = 0
                    for p in vmap:
                        self._get_array_points_(
                            array_points, p.x, p.y, p.cat, i
                        )
                        i += 1

        return array_points

    def _stream_clip(self, stream, aoi_polygon):
        """See base method for description.
        """
        aoi_buffer = self.storage.output_filepath('aoi_buffer')
        Module('v.buffer',
               input=aoi_polygon, output='aoi_buffer',
               distance=-GridGlobals.dx / 3)

        stream_aoi = self.storage.output_filepath('stream_aoi')
        Module('v.clip',
               input=stream, clip=aoi_buffer,
               output=stream_aoi)

        return stream_aoi

    def _stream_direction(self, stream, dem):
        """See base method for description.
        """
        # extract elevation for start/end stream nodes
        Module('g.region', raster=dem)
        columns = ['point_x', 'point_y']
        for what in ('start', 'end'):
            Module('v.to.points',
                   input=stream, use=what,
                   output=what)
            column = 'elev_{}'.format(what)
            Module('v.what.rast',
                   map=what, raster=dem,
                   column=column)
            Module('v.db.join',
                   map=stream, column=self.storage.primary_key,
                   other_table=what+'_1', # v.what produces two tables
                   other_column=self.storage.primary_key,
                   subset_columns=[column]
            )

            if what == 'end':
                columns = list(map(lambda x: x + '_end', columns))
            Module('v.to.db',
                   map=stream, option=what,
                   columns=columns
            )
            
            self.__remove_temp_data({'name': what, 'type': 'vector'})

        # flip stream
        stream_flip = []
        with Vector(stream) as vmap:
            vmap.table.filters.select(self.storage.primary_key, 'elev_start', 'elev_end')
            for row in vmap.table:
                if row[1] < row[2]:
                    stream_flip.append(row[0])
        if stream_flip:
            Module('v.edit',
                   map=stream,
                   tool='flip',
                   cats=','.join(stream_flip))

        # add to_node attribute
        Module('v.db.addcolumn',
               map=stream,
               columns=['to_node integer'])
        to_node = {}
        with VectorTopo(stream) as vmap:
            for line in vmap:
                start, end = line.nodes()
                cat = line.cat
                to_node[cat] = GridGlobals.NoDataValue
                for start_line in start.lines():
                    if start_line.cat != cat:
                        to_node[cat] = start_line.cat

        if to_node:
            # TODO: rewrite using pygrass
            # ML: compare with ArcGIS
            tmpfile = tempfile(create=False)
            with open(tmpfile, 'w') as fd:
                for c, n in to_node.items():
                    fd.write('UPDATE {} SET to_node = {} WHERE {} = {};\n'.format(
                        stream, n, self.storage.primary_key, c
                    ))
            Module('db.execute',
                   input=tmpfile)

    def _stream_reach(self, stream):
        """See base method for description.
        """
        Module('g.region',
               vector=stream,
               s=GridGlobals.yllcorner, w=GridGlobals.xllcorner,
               n=GridGlobals.yllcorner+(GridGlobals.r * GridGlobals.dy),
               e=GridGlobals.xllcorner+(GridGlobals.c * GridGlobals.dx),
               ewres=GridGlobals.dx, nsres=GridGlobals.dy)

        stream_seg = self.storage.output_filepath('stream_seg')
        Module('v.to.rast',
               input=stream, type='line', use='cat',
               output=stream_seg)

        mat_stream_seg = self._rst2np(stream_seg)
        # ML: is no_of_streams needed (-> mat_stream_seg.max())
        self._get_mat_stream_seg(mat_stream_seg)

        return mat_stream_seg.astype('int16')
        
    def _stream_slope(self, stream):
        """See base method for description.
        """
        Module('v.db.addcolumn',
               map=stream,
               columns=['slope double precision'])

        Module('v.to.db',
               map=stream,
               columns='shape_length',
               option='length')
        Module('v.db.update',
               map=stream,column='slope',
               query_column='(elev_start - elev_end) / shape_length')

        # ML: compare with AcrGIS
        with Vector(stream) as vmap:
            vmap.table.filters.select(
                self.storage.primary_key, 'slope')
            for row in vmap.table:
                if row[1] == 0:
                    raise DataPreparationError(
                        'Reach FID: {} has zero slope'.format(row[0]))

    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        """See base method for description.
        """
        stream_shape_tab = self.__qualified_name(
            stream_shape_tab, mtype='table')['name']
        Module('db.copy',
               from_table=stream_shape_tab,
               from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db',
               to_table=stream_shape_tab)
        Module('v.db.join',
               map=stream, column=stream_shape_code,
               other_table=stream_shape_tab,
               other_column=stream_shape_code,
               subset_columns=self.stream_shape_fields)

        stream_attr = self._stream_attr_(self.storage.primary_key)
        with Vector(stream) as vmap:
            vmap.table.filters.select(*stream_attr.keys())
            for row in vmap.table:
                i = 0
                fields = list(stream_attr.keys())
                for i in range(len(row)):
                    if row[i] in (" ", None):
                        raise DataPreparationError(
                            "Empty value in tab_stream_shape ({}) found.".format(fields[i])
                        )
                    stream_attr[fields[i]].append(row[i])
                    i += 1

        stream_attr['fid'] = stream_attr.pop(self.storage.primary_key)

        return stream_attr
                    
    def _check_input_data(self):
        """See base method for description.
        """
        def _check_empty_values(table, field):
            try:
                with Vector(**table) as vmap:
                    vmap.table.filters.select(field, self.storage.primary_key)
                    for row in vmap.table:
                        if row[0] in (None, ""):
                            raise DataPreparationInvalidInput(
                                "'{}' values in '{}' table are not correct, "
                                "empty value found in row {})".format(field, table, row[1])
                            )
            except OpenError as e:
                raise DataPreparationInvalidInput(e)

        _check_empty_values(
            self.__qualified_name(self._input_params['vegetation']),
            self._input_params['vegetation_type']
        )
        _check_empty_values(
            self.__qualified_name(self._input_params['soil']),
            self._input_params['soil_type']
        )

        
        if self._input_params['table_stream_shape']:
            table = Table(**self.__qualified_name(self._input_params['table_stream_shape'], mtype='table'))
            fields = table.columns.names()
            for f in self.stream_shape_fields:
                if f not in fields:
                    raise DataPreparationInvalidInput(
                        "Field '{}' not found in '{}'\nProper columns codes are: {}".format(
                            f, self._input_params['table_stream_shape'], self.stream_shape_fields)
                    )

        # overlapping polygons (soils)
        try:
            with VectorTopo(**self.__qualified_name(self._input_params['soil'])) as fd:
                for area in fd.viter('areas'):
                    cats = list(area.cats().get_list())
                    if len(cats) > 1:
                        raise DataPreparationInvalidInput(
                            "overlapping soil polygons detected"
                        )
        except OpenError as e:
            raise DataPreparationInvalidInput(e)
