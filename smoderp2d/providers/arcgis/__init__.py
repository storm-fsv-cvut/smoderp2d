import os
import sys
import logging

import arcpy

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider, CompType
from smoderp2d.providers.arcgis import constants
from smoderp2d.providers.arcgis.logger import ArcPyLogHandler
from smoderp2d.providers import Logger

class ArcGisProvider(BaseProvider):
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        self._print_fn = self._print_logo_fn = arcpy.AddMessage

        # output directory must be defined for _cleanup() method
        Globals.outdir = self._get_argv(
            constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY
        )

        # computation type
        if self._get_argv(constants.PARAMETER_DPRE_ONLY):
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
       
        prep = PrepareData()
        return prep.run()
