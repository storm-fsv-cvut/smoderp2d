from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.data_preparation import PrepareDataBase
from smoderp2d.providers.grass.terrain import compute_products

import grass.script as gs

class PrepareData(PrepareDataBase):
    def __init__(self, options):
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
