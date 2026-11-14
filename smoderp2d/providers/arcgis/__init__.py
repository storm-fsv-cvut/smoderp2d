import os
import logging
import shutil

import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers.base import BaseProvider, BaseWriter, WorkflowMode
from smoderp2d.providers.arcgis.logger import ArcPyLogHandler
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError

try:
    import arcpy
except RuntimeError as e:
    raise ProviderError("ArcGIS provider: {}".format(e))


class ArcGisWriter(BaseWriter):
    def __init__(self):
        super(ArcGisWriter, self).__init__()

        # Overwriting output
        arcpy.env.overwriteOutput = 1

    def create_storage(self, outdir):
        # create core ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(outdir, "data.gdb")

        # create temporary ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(os.path.join(outdir, 'temp'), "data.gdb")

        # create control ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(
            os.path.join(outdir, 'control'), "data.gdb"
        )

    def output_filepath(self, name):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :return: full path to the dataset
        """
        path = os.path.join(
            BaseWriter.output_filepath(self, name, dirname_only=True),
            'data.gdb',
            name
        )
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
            array.filled(GridGlobals.NoDataValue) if isinstance(array, ma.MaskedArray) else array,
            lower_left, GridGlobals.dx, GridGlobals.dy,
            value_to_nodata=GridGlobals.NoDataValue
        )

        arcpy.RasterToASCII_conversion(
            raster,
            file_output + self._raster_extension
        )


class ArcGisProvider(BaseProvider):
    def __init__(self, log_handler=ArcPyLogHandler):
        super(ArcGisProvider, self).__init__()

        # options must be defined by set_options()
        self._options = None

        # logger
        self.add_logging_handler(
            handler=log_handler(),
            formatter=logging.Formatter("%(levelname)-8s %(message)s")
        )

        # define storage writer
        self.storage = ArcGisWriter()

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

    def _postprocessing(self):
        """See base method for description."""
        # here ArcGIS-specific postprocessing starts...
        Logger.debug('ArcGIS-specific postprocessing')
        if not self._options['generate_temporary']:
            try:
                # delete temporary data
                data_dir = os.path.join(Globals.outdir, 'temp')
                arcpy.Delete_management(os.path.join(data_dir, "data.gdb"))
                shutil.rmtree(data_dir)
            except PermissionError as e:
                raise ProviderError(
                    f"Unable to cleanup output temporary directory: {e}"
                )
