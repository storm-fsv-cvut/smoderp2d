import math
from subprocess import PIPE

import numpy as np

from smoderp2d.providers.grass.terrain import compute_products
from smoderp2d.providers.grass.manage_fields import ManageFields

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput
from smoderp2d.providers.base.data_preparation import PrepareDataBase

from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo
from grass.pygrass.raster import RasterRow, raster2numpy

class PrepareData(PrepareDataBase, ManageFields):
    def __init__(self, options):
        super(PrepareData, self).__init__()

        # get input parameters
        self._get_input_params(options)

    def __del__(self):
        # remove mask
        Module('r.mask',
               flags='r'
        )

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
        Module('g.region',
               raster=dem
        )
        Module('r.mask',
               raster=dem
        )
        # not needed to creare raster (just for comparision with ArcGIS)
        Module('r.mapcalc',
               expression='{} = 1'.format(self._data['dem_mask'])
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
               output=self._data['vector_mask'],
               type='area'
        )

        # dissolve soil and vegetation polygons
        Module('v.dissolve',
               input=vegetation,
               output=self._data['vegetation_boundary'],
               column=vegetation_type
        )
        Module('v.dissolve',
               input=soil,
               output=self._data['soil_boundary'],
               column=soil_type
        )

        # do intersection
        Module('v.overlay',
               ainput=self._data['vegetation_boundary'],
               binput=self._data['vector_mask'],
               operator='and',
               olayer='1,1,0',
               output=self._data['vegetation_mask']
        )
        Module('v.overlay',
               ainput=self._data['soil_boundary'],
               binput=self._data['vector_mask'],
               operator='and',
               olayer='1,1,0',
               output=self._data['soil_mask']
        )
        Module('v.overlay',
               ainput=self._data['vegetation_mask'],
               binput=self._data['soil_mask'],
               operator='and',
               olayer='1,1,1',
               output=self._data['intersect']
        )

        # remove "soil_veg" if exists and create a new one
        Module('v.db.dropcolumn',
               map=self._data['intersect'],
               columns=self._data['soil_veg_column']
        )
        Module('v.db.addcolumn',
               map=self._data['intersect'],
               columns='{} varchar(255)'.format(
                   self._data['soil_veg_column'])
        )

        # compute "soil_veg" values (soil_type + vegetation_type)
        vtype1 = vegetation_type + "_1" if soil_type == vegetation_type else vegetation_type
        Module('v.db.update',
               map=self._data['intersect'],
               column=self._data['soil_veg_column'],
               query_column='b_a_{} || a_a_{}'.format(
                   soil_type, vtype1)
        )

        # copy attribute table for modifications
        Module('db.copy',
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

        # TODO: rewrite into pygrass syntax
        ret = Module('v.db.select',
                     flags='c',
                     map=self._data['intersect'],
                     columns=self._data['sfield'],
                     where=' or '.join(
                         list(map(lambda x: '{} is NULL'.format(x), self._data['sfield']))),
                     stdout_=PIPE
        )
        if len(ret.outputs.stdout) > 0:
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
        Module('g.region',
               vector=intersect,
               align=dem
        )

        Module('v.to.rast',
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
            Module('r.mapcalc',
                   expression='{o} = if(isnull({m}), null(), {i})'.format(
                       o=outmap, m=self._data['inter_mask'], i=inmap
            ))

        return self._data['dem_clip'], self._data['slope_clip'], self._data['flow_clip'] if flow_direction else None

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
               output=self._data['points_mask']
        )
        # count number of features
        npoints = self.get_num_points(self.data['points'])
        npoints_clipped = self.get_num_points(self._data['points_mask'])

        self._diff_npoints(npoints, npoints_clipped)

        self.data['points'] = self._data['points_mask']

    def _rst2np(self, raster):
        """
        Convert raster data into numpy array

        :param raster: raster name

        :return: numpy array
        """
        Module('g.region',
               raster=raster
        )
        return raster2numpy(raster)

    def _get_raster_dim(self, dem_clip):
        """
        Get raster spatial reference info.

        :param dem_clip: clipped dem raster map
        """
        with RasterRow(dem_clip) as data:
            # lower left corner coordinates
            self.data['xllcorner'] = data.info.west
            self.data['yllcorner'] = data.info.south
            self.data['vpix'] = data.info.nsres
            self.data['spix'] = data.info.ewres

        self.data['NoDataValue'] = None
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
               elevation=dem_clip,
               aspect=asp
        )
        asppii = 'asppii'
        Module('r.mapcalc',
               expression='{} = {} * {}'.format(
                   asppii, asp, pii
        ))
        sinasp = 'sinasp'
        Module('r.mapcalc',
               expression='{} = sin({})'.format(
                   sinasp, asppii
        ))
        cosasp = 'cosasp'
        Module('r.mapcalc',
               expression='{} = cos({})'.format(
                   cosasp, asppii
        ))
        sinslope = 'sinslope'
        Module('r.mapcalc',
               expression='{} = abs({})'.format(
                   sinslope, sinasp
        ))
        cosslope = 'cosasp'
        Module('r.mapcalc',
               expression='{} = cos({})'.format(
                   cosslope, cosasp
        ))
        times1 = self._data['ratio_cell']
        Module('r.mapcalc',
               expression='{} = {} + {}'.format(
                   times1, cosslope, sinslope
        ))

        efect_cont = self._data['efect_cont']
        Module('r.mapcalc',
               expression='{} = {} * {}'.format(
                   efect_cont, times1, self.data['spix']
        ))
        self.data['mat_efect_cont'] = self._rst2np(efect_cont)

    @staticmethod
    def _streamPreparation(args):
        from smoderp2d.providers.grass.stream_preparation import StreamPreparation

        return StreamPreparation(args).prepare()
