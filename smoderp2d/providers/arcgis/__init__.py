import os
import sys
import logging

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers.base import BaseProvider, CompType, BaseWritter
from smoderp2d.providers.arcgis.logger import ArcPyLogHandler
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError

try:
    import arcpy
except RuntimeError as e:
    raise ProviderError("ArcGIS provider: {}".format(e))

class ArcGisWritter(BaseWritter):
    def __init__(self):
        super(ArcGisWritter, self).__init__()

        # Overwriting output
        arcpy.env.overwriteOutput = 1

    def create_storage(self, outdir):
        # create core ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(outdir, "data.gdb")

        # create temporary ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(os.path.join(outdir, 'temp'), "data.gdb")

        # create control ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(os.path.join(outdir, 'control'), "data.gdb")

    def output_filepath(self, name):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :return: full path to the dataset
        """
        item = self._data_target.get(name)
        if item is None or item not in ("temp", "control", "core"):
            raise ProviderError("Unable to define target in output_filepath: {}".format(name))

        path = Globals.get_outdir()
        # 'core' datasets don't have directory, only the geodatabase
        if item in ("temp", "control"):
            path = os.path.join(path, item)

        path = os.path.join(path, 'data.gdb', name)

        Logger.debug('File path: {}'.format(path))

        return path

    def _write_raster(self, array, file_output):
        """See base method for description.
        """
        self._check_globals()

        lower_left = arcpy.Point(
            GridGlobals.xllcorner,
            GridGlobals.yllcorner,
        )
        
        raster = arcpy.NumPyArrayToRaster(
            array, lower_left, GridGlobals.dx, GridGlobals.dy,
            value_to_nodata=GridGlobals.NoDataValue
        )
        
        arcpy.RasterToASCII_conversion(
            raster,
            file_output
        )

class ArcGisProvider(BaseProvider):
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        # type of computation (default)
        self.args.typecomp = CompType.full

        # options must be defined by set_options()
        self._options = None

        # logger
        self.add_logging_handler(
            handler=ArcPyLogHandler(),
            formatter=logging.Formatter("%(levelname)-8s %(message)s")
        )
        
        # define storage writter
        self.storage = ArcGisWritter()

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._options = options

        # set output directory
        Globals.outdir = options['output']

    def _load_dpre(self):
        """Run data preparation procedure.

        :return dict: loaded data
        """
        if not self._options:
            raise ProviderError("No options given")

        from smoderp2d.providers.arcgis.data_preparation import PrepareData
        prep = PrepareData(self._options, self.storage)
        return prep.run()
