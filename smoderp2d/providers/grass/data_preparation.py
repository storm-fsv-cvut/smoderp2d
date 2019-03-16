import math
import numpy as np

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput
from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

import grass.script as gs
from grass.script import array as garray

class PrepareData(PrepareDataBase, ManageFields):
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

    def _clip_data(self, dem, intersect, slope, flow_direction):
        """
        Clip input data based on AOI.

        :param str dem: raster DTM name
        :param str intersect: vector intersect feature call name
        :param str slope: raster slope name
        :param str flow_direction: raster flow direction name

        :return str dem_clip: output clipped DTM name
        :return str slope_clip: output clipped slope name
        :return str flow_direction_clip: ouput clipped flow direction name

        """
        if self.data['points']:
            self._clip_points(intersect)

        # set computation region
        gs.run_command('g.region',
                       vector=intersect,
                       align=dem
        )

        gs.run_command('v.to.rast',
                       input=intersect,
                       type='area',
                       use='val',
                       output=self._data['inter_mask']
        )

        # cropping rasters
        # using r.mapcalc since r.clip is not available in core
        for inmap, outmap in ((dem, self._data['dem_clip']),
                              (slope, self._data['slope_clip']),
                              (flow_direction, self._data['flow_clip'])):
            if inmap is None:
                # flow direction can be None
                continue
            gs.run_command(
                'r.mapcalc',
                expression='{o} = if(isnull({m}), null(), {i})'.format(
                    o=outmap, m=self._data['inter_mask'], i=inmap
                ))

        return self._data['dem_clip'], self._data['slope_clip'], self._data['flow_clip'] if flow_direction else None

    def _clip_points(self, intersect):
        """
        Clip input points data.

        :param intersect: vector intersect feature class
        """
        gs.run_command('v.clip',
                       input=self.data['points'],
                       clip=intersect,
                       output=self._data['points_mask']
        )
        # count number of features
        npoints = gs.vector_info_topo(self.data['points'])['points']
        npoints_clipped = gs.vector_info_topo(self._data['points_mask'])['points']

        self._diff_npoints(npoints, npoints_clipped)

        self.data['points'] = self._data['points_mask']

    def _rst2np(self, raster):
        """
        Convert raster data into numpy array

        :param raster: raster name

        :return: numpy array
        """
        gs.run_command('g.region',
                       raster=raster
        )
        map_array = garray.array()
        map_array.read(raster)

        return map_array

    def _get_raster_dim(self, dem_clip):
        """
        Get raster spatial reference info.

        :param dem_clip: clipped dem raster map
        """
        dem_desc = gs.raster_info(dem_clip)

        # lower left corner coordinates
        self.data['xllcorner'] = dem_desc['west']
        self.data['yllcorner'] = dem_desc['south']
        self.data['NoDataValue'] = None
        self.data['vpix'] = dem_desc['nsres']
        self.data['spix'] = dem_desc['ewres']
        self.data['pixel_area'] = self.data['spix'] * self.data['vpix']

        # size of the raster [0] = number of rows; [1] = number of columns
        self.data['r'] = self.data['mat_dem'].shape[0]
        self.data['c'] = self.data['mat_dem'].shape[1]

    def _get_attrib(self, sfield, intersect):
        """
        Get numpy arrays of selected attributes.

        :param sfield: list of attributes
        :param intersect: vector intersect name

        :return all_atrib: list of numpy array
        """
        all_attrib = self._get_attrib_(sfield, intersect)

        idx = 0
        for field in sfield:
            output = "r{}".format(field)
            gs.run_command('v.to.rast',
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
            count = gs.vector_info_topo(self.data['points'])['points']

            # empty array
            self.data['array_points'] = np.zeros([int(count), 5], float)

            ret = gs.read_command(
                'v.out.ascii',
                input=self.data['points'],
                separator=';'
            )
            i = 0
            for row in ret.splitlines():
                x, y, cat = row.split(';')

                i = self._get_array_points_(
                    float(x), float(y), int(cat), i
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
        gs.run_command('r.slope.aspect',
                       elevation=dem_clip,
                       aspect=asp
        )
        asppii = 'asppii'
        gs.run_command('r.mapcalc',
                       expression='{} = {} * {}'.format(
                           asppii, asp, pii
        ))
        sinasp = 'sinasp'
        gs.run_command('r.mapcalc',
                       expression='{} = sin({})'.format(
                           sinasp, asppii
        ))
        cosasp = 'cosasp'
        gs.run_command('r.mapcalc',
                       expression='{} = cos({})'.format(
                           cosasp, asppii
        ))
        sinslope = 'sinslope'
        gs.run_command('r.mapcalc',
                       expression='{} = abs({})'.format(
                           sinslope, sinasp
        ))
        cosslope = 'cosasp'
        gs.run_command('r.mapcalc',
                       expression='{} = cos({})'.format(
                           cosslope, cosasp
        ))
        times1 = 'times1'
        gs.run_command('r.mapcalc',
                       expression='{} = {} + {}'.format(
                           times1, cosslope, sinslope
        ))
        # times1.save(os.path.join(self.data['temp'], "ratio_cell"))

        efect_cont = 'efect_cont'
        gs.run_command('r.mapcalc',
                       expression='{} = {} * {}'.format(
                           efect_cont, times1, self.data['spix']
        ))
        # efect_cont.save(os.path.join(self.data['temp'], "efect_cont"))
        self.data['mat_efect_cont'] = self._rst2np(efect_cont)
