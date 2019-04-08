import os
import logging

from smoderp2d.providers.base import BaseProvider, CompType

from smoderp2d.core.general import Globals
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.grass.logger import GrassGisLogHandler
from smoderp2d.providers import Logger

import grass.script as gs

class GrassGisProvider(BaseProvider):
    def __init__(self):
        super(GrassGisProvider, self).__init__()

        self._print_fn = gs.message

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
        if list(map(int, gs.version()['version'].split('.')[:-1])) < [7, 7]:
            raise ProviderError("GRASS GIS version 7.8+ required")

        # force overwrite
        os.environ['GRASS_OVERWRITE'] = '1'

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._options = options

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        if not self._options:
            raise ProviderError("No options given")
        from smoderp2d.providers.grass.data_preparation import PrepareData

        prep = PrepareData(self._options)
        return prep.run()
