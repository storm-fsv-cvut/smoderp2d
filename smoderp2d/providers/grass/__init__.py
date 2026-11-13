import os
import sys
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

class GrassGisWriter(BaseWriter):
    _vector_extension = '.gml'

    def __init__(self):
        super(GrassGisWriter, self).__init__()

        # primary key
        self.primary_key = "cat"

    def output_filepath(self, name, full_path=False):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :param full_path: True return full path otherwise only dataset name

        :return: full path to the dataset
        """
        if full_path:
            return BaseWriter.output_filepath(self, name)
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

        self.export_raster(raster_name, file_output)

    def export_raster(self, raster_name, file_output):
        """Export GRASS raster map to output data format.

        :param raster_name: GRASS raster map name
        :param file_output: Target file path
        """
        Module(
            'r.out.gdal',
            input=raster_name,
            output=file_output + self._raster_extension,
            format='AAIGrid',
            nodata=GridGlobals.NoDataValue,
            type='Float64',
            overwrite=True,
        )

    def export_vector(self, raster_name, file_output):
        """Export GRASS vector map to output data format.

        :param raster_name: GRASS raster map name
        :param file_output: Target file path
        """
        Module(
            'v.out.ogr',
            flags='s',
            input=raster_name,
            output=file_output + self._vector_extension,
            format='GML',
            overwrite=True,
        )


class GrassGisProvider(BaseProvider):

    def __init__(self, log_handler=GrassGisLogHandler):
        super(GrassGisProvider, self).__init__()

        # options must be defined by set_options()
        self._options = None

        # logger
        self.add_logging_handler(
            handler=log_handler(),
            formatter=logging.Formatter("%(message)s")
        )

        # force overwrite
        os.environ['GRASS_OVERWRITE'] = '1'
        # be quiet
        os.environ['GRASS_VERBOSE'] = '0'
        # allow to run r.hydrodem also when compatibility test fails
        os.environ['GRASS_COMPATIBILITY_TEST'] = '0'

        # define storage writer
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

    def _postprocessing(self):
        """See base method for description."""
        # here GRASS-specific postprocessing starts...
        Logger.debug('GRASS-specific postprocessing')
