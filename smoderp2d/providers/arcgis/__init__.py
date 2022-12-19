import os
import sys
import logging

import arcpy

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers.base import BaseProvider, CompType, BaseWritter
from smoderp2d.providers.arcgis.logger import ArcPyLogHandler
from smoderp2d.providers import Logger
from smoderp2d.exceptions import GlobalsNotSet, ProviderError


class ArcGisWritter(BaseWritter):
    def __init__(self):
        super(ArcGisWritter, self).__init__()

        # primary key depends of storage format
        # * Shapefile -> FID
        # * FileGDB -> OBJECTID
        self.primary_key = "OBJECTID"

        # Overwriting output
        arcpy.env.overwriteOutput = 1

    def create_storage(self,outdir):
        # create core ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(outdir, "data.gdb")

        # create temporary ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB( os.path.join(outdir, 'temp'), "data.gdb")

        # create control ArcGIS File Geodatabase
        arcpy.management.CreateFileGDB(os.path.join(outdir, 'control'), "data.gdb")

    def set_data_target(self, data):
        self._data_target = data

    def output_filepath(self, name):
        """Get ArcGIS data path.

        TODO: item needs to be set for each raster 
        reparatelly. Now all is in temp dir.

        :param name: layer name
        :param item: target item (temp, control)
        """
        item = self._data_target.get(name)
        if item not in (None, "temp", "control"):
            raise ProviderError("Invalid item for output_filepath: {}".format(item))

        path = Globals.get_outdir()
        if item:
            path = os.path.join(path, item)
        path = os.path.join(path, 'data.gdb', name)

        Logger.debug('File path: {}'.format(path))

        return path

    def write_raster(self, array, output_name, directory=''):
        """Write raster (numpy array) to ASCII file.

        :param array: numpy array
        :param output_name: output filename
        :param directory: directory where to write output file
        """
        file_output = self._raster_output_path(output_name, directory)
        
        # prevent call globals before values assigned
        if (GridGlobals.xllcorner == None):
            raise GlobalsNotSet()
        if (GridGlobals.yllcorner == None):
            raise GlobalsNotSet()
        if (GridGlobals.dx == None):
            raise GlobalsNotSet()
        if (GridGlobals.dy == None):
            raise GlobalsNotSet()

        lower_left = arcpy.Point(
            GridGlobals.xllcorner,
            GridGlobals.yllcorner,
        )
        raster = arcpy.NumPyArrayToRaster(
            array, lower_left, GridGlobals.dx, GridGlobals.dy,
            value_to_nodata=GridGlobals.NoDataValue)
        arcpy.RasterToASCII_conversion(
            raster,
            file_output
        )

        self._print_array_stats(
            array, file_output
        )

class ArcGisProvider(BaseProvider):
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        self._print_fn = self._print_logo_fn = arcpy.AddMessage

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
        from smoderp2d.providers.arcgis.data_preparation import PrepareData
       
        prep = PrepareData(self._options, self.storage)
        return prep.run()
