import os
import logging

from smoderp2d.providers.base import BaseProvider, CompType

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.grass.logger import GrassGisLogHandler
from smoderp2d.providers import Logger

import grass.script as gs
from grass.pygrass.gis import Region
from grass.pygrass.modules import Module
from grass.pygrass.raster import numpy2raster
from grass.pygrass.messages import Messenger

class GrassGisProvider(BaseProvider):
    def __init__(self):
        super(GrassGisProvider, self).__init__()

        msgr = Messenger()
        self._print_fn = msgr.message

        # type of computation (default)
        self.args.typecomp = CompType.full

        # options must be defined by set_options()
        self._options = None

        # logger
        self._add_logging_handler(
            handler=GrassGisLogHandler(),
            formatter = logging.Formatter("%(message)s")
        )

        # check version
        # TBD: change to pygrass API
        if list(map(int, gs.version()['version'].split('.')[:-1])) < [7, 7]:
            raise ProviderError("GRASS GIS version 7.8+ required")

        # force overwrite
        os.environ['GRASS_OVERWRITE'] = '1'
        # be quiet
        os.environ['GRASS_VERBOSE'] = '1'

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._options = options

        # set output directory
        Globals.outdir = options['output_dir']

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        if not self._options:
            raise ProviderError("No options given")
        from smoderp2d.providers.grass.data_preparation import PrepareData

        prep = PrepareData(self._options)
        return prep.run()

    def _raster_output(self, arr, output):
        """Write raster to ASCII file.

        :param arr: numpy array
        :param output: output filename
        """
        # set output region
        region = Region()
        region.west = GridGlobals.xllcorner
        region.south = GridGlobals.xllcorner
        # TODO: use pygrass API instead
        region.east = region.west + (GridGlobals.c * GridGlobals.dx)
        region.north = region.south + (GridGlobals.r * GridGlobals.dy)
        region.cols = GridGlobals.c
        region.rows = GridGlobals.r
        region.write()

        # TBD: extend pygrass to export array directly to specified
        # external format
        numpy2raster(
            arr, "FCELL",
            output, overwrite=True
        )

        file_output = self._raster_output_path(output)

        Module('r.out.gdal',
               input=output,
               output=file_output,
               format='AAIGrid',
               nodata=GridGlobals.NoDataValue,
               overwrite=True
        )

        self._print_arr_stats(arr)
        Logger.info("Raster ASCII output file {} saved".format(file_output))
