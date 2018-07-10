import sys

import arcpy

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider
from smoderp2d.providers.arcgis import constants

class ArcGisProvider(BaseProvider):
    
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        self._print_fn = arcpy.AddMessage

        # ArcGIS provider is designed to support only 'full' type of
        # computation
        self._args.typecomp = 'full'

        # must be defined for _cleanup() method
        Globals.outdir = self._get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)

    @staticmethod
    def _get_argv(idx):
        return sys.argv[idx+1]

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        from smoderp2d.providers.arcgis.data_preparation import PrepareData
       
        prep = PrepareData()
        return prep.run()
