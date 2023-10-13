import os
import logging

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import BaseProvider, BaseWriter, WorkflowMode
from smoderp2d.providers.grass.logger import GrassGisLogHandler
from smoderp2d.providers import Logger

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.modules import Module
from grass.pygrass.raster import numpy2raster
from grass.pygrass.messages import Messenger


class GrassGisWriter(BaseWriter):
    def __init__(self):
        super(GrassGisWriter, self).__init__()

        # primary key
        self.primary_key = "cat"

    def output_filepath(self, name):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :return: full path to the dataset
        """
        # TODO: how to deal with temp/core...?
        return name

    def _write_raster(self, array, file_output):
        """See base method for description.
        """
        self._check_globals()

        # set output region (use current region when GridGlobals are not set)
        if GridGlobals.r:
            region = Region()
            region.west = GridGlobals.xllcorner
            region.south = GridGlobals.yllcorner
            # TODO: use pygrass API instead
            region.east = region.west + (GridGlobals.c * GridGlobals.dx)
            region.north = region.south + (GridGlobals.r * GridGlobals.dy)
            region.cols = GridGlobals.c
            region.rows = GridGlobals.r
            region.write()

        raster_name = os.path.splitext(os.path.basename(file_output))[0]

        numpy2raster(
            array, "FCELL",
            raster_name, overwrite=True
        )

        Module('r.out.gdal',
               input=raster_name,
               output=file_output,
               format='AAIGrid',
               nodata=GridGlobals.NoDataValue,
               overwrite=True
        )


class GrassGisProvider(BaseProvider):

    def __init__(self, log_handler=GrassGisLogHandler):
        super(GrassGisProvider, self).__init__()

        # type of computation (default)
        self.args.workflow_mode = WorkflowMode.full

        # options must be defined by set_options()
        self._options = None

        # logger
        self.add_logging_handler(
            handler=log_handler(),
            formatter = logging.Formatter("%(message)s")
        )

        # check version
        # TBD: change to pygrass API
        if list(map(int, gs.version()['version'].split('.')[:-1])) < [8, 3]:
            raise ProviderError("GRASS GIS version 8.3+ required")

        # force overwrite
        os.environ['GRASS_OVERWRITE'] = '1'
        # be quiet
        os.environ['GRASS_VERBOSE'] = '-1'

        # define storage writter
        self.storage = GrassGisWriter()

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._options = options

        # set output directory
        Globals.outdir = options['output']

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        if not self._options:
            raise ProviderError("No options given")

        from smoderp2d.providers.grass.data_preparation import PrepareData
        prep = PrepareData(self._options, self.storage)
        return prep.run()
