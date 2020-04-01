import os
import sys
import logging

import arcpy

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers.base import BaseProvider, CompType, BaseWritter
from smoderp2d.providers.arcgis import constants
from smoderp2d.providers.arcgis.logger import ArcPyLogHandler
from smoderp2d.providers import Logger
from smoderp2d.exceptions import GlobalsNotSet

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
        arcpy.CreateFileGDB_management(
            outdir,
            "data.gdb")

        # create temporary ArcGIS File Geodatabase
        arcpy.CreateFileGDB_management(
            os.path.join(outdir, 'temp'),
            "data.gdb")

        # create control ArcGIS File Geodatabase
        arcpy.CreateFileGDB_management(
            os.path.join(outdir, 'control'),
            "data.gdb")

    def output_filepath(self, name, item='temp'):
        """Get ArcGIS data path.

        TODO: item needs to be set for each raster 
        reparatelly. Now all is in temp dir.

        :param name: layer name

        :return: full path
        """
        #try:
        #    item = self._data[name]
        #except:
        #    item = 'temp'

        path = os.path.join(
            Globals.get_outdir(), item, 'data.gdb', name
        )
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

        # output directory must be defined for _cleanup() method
        Globals.outdir = self._get_argv(
            constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY
        )

        # computation type
        if self._get_argv(constants.PARAMETER_DPRE_ONLY).lower() == 'true':
            self.args.typecomp = CompType.dpre
            self.args.data_file = os.path.join(
                Globals.outdir, 'save.pickle'
            )
        else:
            self.args.typecomp = CompType.full

        # logger
        self._add_logging_handler(
            handler=ArcPyLogHandler(),
            formatter=logging.Formatter("%(levelname)-8s %(message)s")
        )
        
        # define storage writter
        self.storage = ArcGisWritter()

    @staticmethod
    def _get_argv(idx):
        """Get argument by index.

        :param int idx: index
        """
        return sys.argv[idx+1]

    def _load_dpre(self):
        """Run data preparation procedure.

        :return dict: loaded data
        """
        from smoderp2d.providers.arcgis.data_preparation import PrepareData
       
        prep = PrepareData(self.storage)
        return prep.run()
