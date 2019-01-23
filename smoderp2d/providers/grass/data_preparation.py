from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.base.exception import DataPreparationInvalidInput

import grass.script as gs

class PrepareData(PrepareDataBase):
    def __init__(self, options):
        super(PrepareData, self).__init__()

        # get input parameters
        self._get_input_params(options)

    def _get_input_params(self, options):
        """Get input parameters from ArcGIS toolbox.
        """
        self._input_params = options
        # output directory not defined by GRASS (data are written into
        # current mapset by default)
        self._input_params['output'] = None

    def _set_mask(self):
        """Set mask from elevation map.

        Also sets computational region.

        :return: copy, mask (due to ArcGIS provider)
        """
        dem = self._input_params['elevation']
        gs.run_command('g.region',
                       raster=dem
        )
        gs.run_command('r.mask',
                       raster=dem
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
        gs.run_command('r.to.vect',
                       input='MASK',
                       output=self._data['vector_mask'],
                       type='area'
        )

        # dissolve soil and vegetation polygons
        gs.run_command('v.dissolve',
                       input=vegetation,
                       output=self._data['vegetation_boundary'],
                       column=vegetation_type
        )
        gs.run_command('v.dissolve',
                       input=soil,
                       output=self._data['soil_boundary'],
                       column=soil_type
        )

        # do intersection
        gs.run_command('v.overlay',
                       ainput=self._data['vegetation_boundary'],
                       binput=self._data['vector_mask'],
                       operator='and',
                       olayer='1,1,0',
                       output=self._data['vegetation_mask']
        )
        gs.run_command('v.overlay',
                       ainput=self._data['soil_boundary'],
                       binput=self._data['vector_mask'],
                       operator='and',
                       olayer='1,1,0',
                       output=self._data['soil_mask']
        )
        gs.run_command('v.overlay',
                       ainput=self._data['vegetation_mask'],
                       binput=self._data['soil_mask'],
                       operator='and',
                       olayer='1,1,1',
                       output=self._data['intersect']
        )

        # remove "soil_veg" if exists and create a new one
        gs.run_command('v.db.dropcolumn',
                       map=self._data['intersect'],
                       column=self._data['soil_veg_column']
        )
        gs.run_command('v.db.addcolumn',
                       map=self._data['intersect'],
                       columns='{} varchar(255)'.format(
                           self._data['soil_veg_column'])
        )

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        gs.run_command('v.db.update',
                       map=self._data['intersect'],
                       column=self._data['soil_veg_column'],
                       query_column='b_a_{} || a_a_{}'.format(
                           soil_type, vtype1)
        )

        # copy attribute table for modifications
        gs.run_command('db.copy',
                       from_table=table_soil_vegetation,
                       to_table=self._data['soil_veg_copy'],
                       from_database='$GISDBASE/$LOCATION_NAME/PERMANENT/sqlite/sqlite.db'
        )

        # join table copy to intersect vector map
        self._join_table(
            self._data['intersect'], self._data['soil_veg_column'],
            self._data['soil_veg_copy'], table_soil_vegetation_code,
            ",".join(self._data['sfield'])
        )

        ret = gs.read_command(
            'v.db.select',
            flags='c',
            map=self._data['intersect'],
            columns=self._data['sfield'],
            where=' or '.join(
                list(map(lambda x: '{} is NULL'.format(x), self._data['sfield'])))
        )
        if len(ret) > 0:
            raise DataPreparationInvalidInput(
                "Values in soilveg tab are not correct"
            )

        return self._data['intersect'], self._data['vector_mask'], self._data['sfield']

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
        kwargs = {}
        if fields:
            kwargs['subset_columns'] = fields
        gs.run_command('v.db.join',
                       map=in_data,
                       column=in_field,
                       other_table=join_table,
                       other_column=join_field,
                       **kwargs
        )
