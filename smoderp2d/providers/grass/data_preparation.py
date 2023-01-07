# import os
import math
from subprocess import PIPE

import numpy as np
import sqlite3

from smoderp2d.core.general import GridGlobals

from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput, \
    DataPreparationError, DataPreparationNoIntersection
from smoderp2d.providers.base.data_preparation import PrepareDataBase

from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.vector.table import Table, get_path
from grass.pygrass.raster import RasterRow, raster2numpy
from grass.pygrass.gis import Region
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
        Module('g.remove', flags="f", **kwargs)

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
        """Creates all the needed DEM derivatives in the DEM's
        original extent to avoid raster edge effects. The clipping
        extent could be replaced be AOI border buffered by 1 cell to
        prevent time consuming operations on DEM if the DEM is much
        larger then the AOI.
        """
        pass

    def _clip_raster_layer(self, dataset, outline, name):
        """Clips raster dataset to given polygon."""
        pass

    def _clip_record_points(self, dataset, outline, name):
        """Makes a copy of record points inside the AOI as new
        feature layer and logs those outside AOI.
        """
        pass

    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_outline, table_soil_vegetation):
        """Prepares the combination of soils and vegetation input
        layers. Gets the spatial intersection of both and checks the
        consistency of attribute table.
        """
        pass

    def _rst2np(self, raster):
        """Convert raster data into numpy array."""
        pass

    def _update_raster_dim(self, reference):
        """Update raster spatial reference info.

        This function must be called before _rst2np() is used first
        time.
        """
        pass

    def _get_array_points(self):
        pass

    def _compute_efect_cont(self, dem_clip):
        """Compute efect contour array.
        """
        pass

    def _stream_clip(self, stream, aoi_polygon):
        pass

    def _stream_direction(self, stream, dem_aoi):
        pass

    def _stream_reach(self, stream):
        pass

    def _stream_slope(self, stream):
        pass

    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        pass

    def _check_input_data(self):
        """Check input data.

        Raise DataPreparationInvalidInput on error.
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

#
################################################################################
#

    def _set_mask(self):
        """Set mask from elevation map.

        Also sets computational region.

        :return: copy, mask (due to ArcGIS provider)
        """
        dem = self._input_params['elevation']
        Module('g.region',
               raster=dem
        )
        Module('r.mask',
               raster=dem
        )
        # not needed to creare raster (just for comparision with ArcGIS)
        Module('r.mapcalc',
               expression='{} = if(MASK, 1, null())'.format('dem_mask')
        )

        return dem, dem

    def _terrain_products(self, dem):
        """Computes terrains products.

        :param str dem: DTM raster map name
        
        :return: (filled elevation, flow direction, flow accumulation, slope)
        """
        return compute_products(dem)

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
        # convert mask info polygon vector map
        Module('r.to.vect',
               input='MASK',
               output='vector_mask',
               type='area'
        )

        # dissolve soil and vegetation polygons
        Module('v.dissolve',
               input=vegetation,
               output='vegetation_boundary',
               column=vegetation_type
        )
        Module('v.dissolve',
               input=soil,
               output='soil_boundary',
               column=soil_type
        )

        # do intersections
        Module('v.clip',
               input='vegetation_boundary',
               clip='vector_mask',
               output='vegetation_mask'
        )
        Module('v.clip',
               input='soil_boundary',
               clip='vector_mask',
               output='soil_mask'
        )
        Module('v.overlay',
               ainput='soil_mask',
               binput='vegetation_mask',
               operator='and',
               output='inter_soil_lu'
        )

        # remove "soil_veg" if exists and create a new one
        Module('v.db.dropcolumn',
               map='inter_soil_lu',
               columns=self._data['soil_veg_column']
        )
        Module('v.db.addcolumn',
               map='inter_soil_lu',
               columns='{} varchar(255)'.format(
                   self._data['soil_veg_column'])
        )

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        try:
            Module('v.db.update',
                   map='inter_soil_lu',
                   column=self._data['soil_veg_column'],
                   query_column='a_{} || b_{}'.format(
                   soil_type, vtype1)
            )
        except CalledModuleError as e:
            raise DataPreparationError('{}'.format(e))

        # copy attribute table for modifications
        Module('db.copy',
               from_table=table_soil_vegetation,
               to_table='soil_veg_copy',
               from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db'
        )

        # join table copy to intersect vector map
        self._join_table(
            'inter_soil_lu', self._data['soil_veg_column'],
            'soil_veg_copy', table_soil_vegetation_code,
            self._data['sfield']
        )

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map='inter_soil_lu',
                     columns=self._data['sfield'],
                     where=' or '.join(
                         list(map(lambda x: '{} is NULL'.format(x), self._data['sfield']))),
                     stdout_=PIPE
        )
        if len(ret.outputs.stdout) > 0:
            raise DataPreparationInvalidInput(
                "Values in soilveg tab are not correct"
            )

        return 'inter_soil_lu', 'vector_mask', self._data['sfield']

    def _clip_data(self, dem, intersect):
        """
        Clip input data based on AOI.

        :param str dem: raster DTM name
        :param str intersect: vector intersect feature call name

        :return str dem_clip: output clipped DTM name

        """
        if self.data['points']:
            self._clip_points(intersect)

        # set computation region
        Module('g.region',
               vector=intersect,
               align=dem
        )
        region = Region()
        # set lower left corner coordinates
        GridGlobals.set_llcorner(
            (region.west, region.south)
        )

        # create raster mask for clipping
        Module('v.to.rast',
               input=intersect,
               type='area',
               use='cat',
               output='inter_mask'
        )

        # cropping rasters
        Module('r.mapcalc',
               expression='{o} = if(isnull({m}), null(), {i})'.format(
                   o='dem_clip', m='inter_mask', i=dem
        ))

        return 'dem_clip'

    @staticmethod
    def get_num_points(vector):
        with VectorTopo(vector) as data:
            np = data.number_of("points")
        return np
    
    def _clip_points(self, intersect):
        """
        Clip input points data.

        :param intersect: vector intersect feature class
        """
        Module('v.clip',
               input=self.data['points'],
               clip=intersect,
               output='points_mask'
        )
        # count number of features
        npoints = self.get_num_points(self.data['points'])
        npoints_clipped = self.get_num_points('points_mask')

        self._diff_npoints(npoints, npoints_clipped)

        self.data['points'] = 'points_mask'

    def _rst2np(self, raster):
        """
        Convert raster data into numpy array

        :param raster: raster name

        :return: numpy array
        """
        # raster is read from current computation region
        # g.region cannot be called here,
        # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
        Region().from_rast(raster)
        return raster2numpy(raster)

    def _get_raster_dim(self, dem_clip):
        """
        Get raster spatial reference info.

        :param dem_clip: clipped dem raster map
        """
        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dem'].shape[0]
        self.data['c'] = self.data['mat_dem'].shape[1]

        with RasterRow(dem_clip) as data:
            # lower left corner coordinates
            self.data['xllcorner'] = data.info.west
            self.data['yllcorner'] = data.info.south
            # x/y resolution
            self.data['dy'] = data.info.nsres
            self.data['dx'] = data.info.ewres
            # check data consistency
            # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
            if data.info.rows != self.data['r'] or \
               data.info.cols != self.data['c']:
                raise DataPreparationError(
                    "Data inconsistency ({},{}) vs ({},{})".format(
                        data.info.rows, data.info.cols, self.data['r'], self.data['c']
                ))

        self.data['NoDataValue'] = None
        self.data['pixel_area'] = self.data['dx'] * self.data['dy']

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
            output = "r{}".format(field)
            Module('v.to.rast',
                   input=intersect,
                   type='area',
                   use='attr',
                   attribute_column=field,
                   output=output
            )
            all_attrib[idx] = self._rst2np(output)
            idx += 1

        return all_attrib

    def _get_array_points(self):
        """Get array of points. Points near AOI border are skipped.
        """
        if self.data['points'] and \
           (self.data['points'] != "#") and (self.data['points'] != ""):
            # get number of points
            count = self.get_num_points(self.data['points'])

            # empty array
            self.data['array_points'] = np.zeros([int(count), 5], float)

            i = 0
            with VectorTopo(self.data['points']) as data:
                for p in data:
                    i = self._get_array_points_(
                        float(p.x), float(p.y), int(p.cat), i
                    )
        else:
            self.data['array_points'] = None

    def _get_slope_dir(self, dem_clip):
        """
        ?

        :param dem_clip:
        """
        pii = math.pi / 180.0
        asp = 'aspect'
        Module('r.slope.aspect',
               flags='n',
               elevation=dem_clip,
               aspect=asp + '_grass'
        )
        Module('r.mapcalc',
               expression="{o}=if({i} == 0, -1, {i})".format(
                   o=asp, i=asp + '_grass'
        ))

        # not needed, GRASS's sin() assumes degrees
        # asppii = 'asppii'
        # Module('r.mapcalc',
        #        expression='{} = {} * {}'.format(
        #            asppii, asp, pii
        # ))
        ratio = 'ratio_cell'
        Module('r.mapcalc',
               expression='{o} = abs(sin({a})) + abs(cos({a}))'.format(
                   o=ratio, a=asp
        ))

        efect_cont = 'efect_cont'
        Module('r.mapcalc',
               expression='{} = {} * {}'.format(
                   efect_cont, ratio, self.data['dx']
        ))
        self.data['mat_efect_cont'] = self._rst2np(efect_cont)

    def _streamPreparation(self, args):
        from smoderp2d.providers.grass.stream_preparation import StreamPreparation

        return StreamPreparation(args, writter=self.storage).prepare()
