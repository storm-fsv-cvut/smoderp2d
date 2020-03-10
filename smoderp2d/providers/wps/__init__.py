import sys
import logging
if sys.version_info.major >= 3:
    from configparser import ConfigParser, NoSectionError
else:
    from ConfigParser import ConfigParser, NoSectionError

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider, Logger
from smoderp2d.providers.cmd import CmdWritter
from smoderp2d.exceptions import ConfigError

class WpsProvider(BaseProvider):
    def __init__(self):
        """WPS provider."""
        super(WpsProvider, self).__init__()

        self._config = ConfigParser()

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._config.read(options['indata'])

        try:
            # set logging level
            Logger.setLevel(self._config.get('Other', 'logging'))
            # sys.stderr logging
            self._add_logging_handler(
                logging.StreamHandler(stream=sys.stderr)
            )

            # must be defined for _cleanup() method
            Globals.outdir = self._config.get('Other', 'outdir')
        except NoSectionError as e:
            raise ConfigError('Config file {}: {}'.format(
                options['indata'], e
            ))

        # define storage writter
        self.storage = CmdWritter()

    def load(self):
        """Load configuration data.

        Only roff procedure supported.
        """
        # cleanup output directory first
        self._cleanup()

        data = self._load_roff(
            self._config.get('Other', 'indata')
        )

        self._set_globals(data)
