import os

from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.grass.terrain import compute_products

import grass.script as gs

class PrepareData(PrepareDataBase):
    def __init__(self, options):
        os.environ['GRASS_OVERWRITE'] = '1'

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

        :return: copy, mask (due to ArcGIS provider)
        """
        elev = self._input_params['elevation']
        gs.run_command('g.region',
                       raster=elev
        )
        gs.run_command('r.mask',
                       raster=elev
        )

        return elev, elev

    def _terrain_products(self, elev):
        return compute_products(elev)
