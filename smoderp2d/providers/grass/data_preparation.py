# import os
import math
from subprocess import PIPE

import numpy as np

from smoderp2d.core.general import GridGlobals

from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput, \
    DataPreparationError
from smoderp2d.providers.base.data_preparation import PrepareDataBase

from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo, Vector
from grass.pygrass.raster import RasterRow, raster2numpy
from grass.pygrass.gis import Region
from grass.exceptions import CalledModuleError, OpenError

class PrepareData(PrepareDataBase, ManageFields):
    def __init__(self, options, writter):
        super(PrepareData, self).__init__(writter)

        # get input parameters
        self._get_input_params(options)

    def __del__(self):
        # remove mask
        try:
            Module('r.mask',
                   flags='r'
            )
        except CalledModuleError:
            pass # mask not exists

    def _get_input_params(self, options):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params = options
        # cast some options to float
        for opt in ('maxdt', 'end_time'):
            self._input_params[opt] = float(self._input_params[opt])
        # TODO: output directory not defined by GRASS (data are written into
        # current mapset by default)
        self._input_params['output'] = None # os.path.join(Location().path(), "output")

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
               expression='{} = 1'.format('dem_mask')
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
               output='vs_intersect'
        )

        # remove "soil_veg" if exists and create a new one
        Module('v.db.dropcolumn',
               map='vs_intersect',
               columns=self._data['soil_veg_column']
        )
        Module('v.db.addcolumn',
               map='vs_intersect',
               columns='{} varchar(255)'.format(
                   self._data['soil_veg_column'])
        )

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        try:
            Module('v.db.update',
                   map='vs_intersect',
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
            'vs_intersect', self._data['soil_veg_column'],
            'soil_veg_copy', table_soil_vegetation_code,
            self._data['sfield']
        )

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map='vs_intersect',
                     columns=self._data['sfield'],
                     where=' or '.join(
                         list(map(lambda x: '{} is NULL'.format(x), self._data['sfield']))),
                     stdout_=PIPE
        )
        if len(ret.outputs.stdout) > 0:
            raise DataPreparationInvalidInput(
                "Values in soilveg tab are not correct"
            )

        return 'vs_intersect', 'vector_mask', self._data['sfield']

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
            self.data['vpix'] = data.info.nsres
            self.data['spix'] = data.info.ewres
            # check data consistency
            # see https://github.com/storm-fsv-cvut/smoderp2d/issues/42
            if data.info.rows != self.data['r'] or \
               data.info.cols != self.data['c']:
                raise DataPreparationError(
                    "Data inconsistency ({},{}) vs ({},{})".format(
                        data.info.rows, data.info.cols, self.data['r'], self.data['c']
                ))

        self.data['NoDataValue'] = None
        self.data['pixel_area'] = self.data['spix'] * self.data['vpix']

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
                   efect_cont, ratio, self.data['spix']
        ))
        self.data['mat_efect_cont'] = self._rst2np(efect_cont)

    def _streamPreparation(self, args):
        from smoderp2d.providers.grass.stream_preparation import StreamPreparation

        return StreamPreparation(args, writter=self.storage).prepare()

    def _check_input_data(self):
        """Check input data.

        """
        # check if input data exists
        for map_name in ('soil',
                         'vegetation'):
            try:
                with Vector(self._input_params[map_name]) as fd:
                    # check if type column exists
                    column_name = self._input_params['{}_type'.format(map_name)]
                    if column_name not in fd.table.columns.names():
                        raise DataPreparationInvalidInput(
                            'Column <{}> does not exist'.format(column_name)
                        )
            except OpenError as e:
                raise DataPreparationInvalidInput(e)

        # soil vector (check for overlaping polygons)
        try:
            with VectorTopo(self._input_params['soil']) as fd:
                for area in fd.viter('areas'):
                    cats = list(area.cats().get_list())
                    if len(cats) > 1:
                        raise DataPreparationInvalidInput(
                            "overlapping soil polygons detected"
                        )
        except OpenError as e:
            raise DataPreparationInvalidInput(e)
