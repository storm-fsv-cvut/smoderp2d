import os
import logging

from smoderp2d.providers.base import BaseProvider, CompType, BaseWritter

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.grass.logger import GrassGisLogHandler
from smoderp2d.providers import Logger

import grass.script as gs
from grass.pygrass.gis import Region
from grass.pygrass.modules import Module
from grass.pygrass.raster import numpy2raster
from grass.pygrass.messages import Messenger

class GrassGisWritter(BaseWritter):
    def __init__(self):
        super(GrassGisWritter, self).__init__()

        # primary key
        self.primary_key = "cat"

    def write_raster(self, array, output_name, directory='core'):
        """Write raster to ASCII file.

        :param array: numpy array
        :param output_name: output filename
        :param directory: directory where to write output file
        """
        # set output region (use current region when GridGlobals are not set)
        if GridGlobals.r:
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
            array, "FCELL",
            output_name, overwrite=True
        )

        file_output = self._raster_output_path(output_name, directory)

        Module('r.out.gdal',
               input=output_name,
               output=file_output,
               format='AAIGrid',
               nodata=GridGlobals.NoDataValue,
               overwrite=True
        )

        self._print_array_stats(
            array, file_output
        )

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

        # define storage writter
        self.storage = GrassGisWritter()

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

        prep = PrepareData(self._options, self.storage)
        return prep.run()
