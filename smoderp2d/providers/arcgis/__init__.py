import sys

import arcpy

from smoderp2d.providers.base import BaseProvider
from smoderp2d.providers.arcgis import constants

class ArcGisProvider(BaseProvider):
    
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        # ArcGIS provider is designed to support only 'full' type of
        # computation
        self._args.typecomp = 'full'

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        from smoderp2d.data_preparation.data_preparation import PrepareData
       
        prep = PrepareData()
        return prep.run()
