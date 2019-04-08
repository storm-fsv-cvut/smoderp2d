import sys
import argparse
import logging
if sys.version_info.major >= 3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider, Logger, CompType

class CmdProvider(BaseProvider):
    def __init__(self):
        """Create argument parser."""
        super(CmdProvider, self).__init__()
        
        # define CLI parser
        parser = argparse.ArgumentParser(description='Run Smoderp2D.')

        # type of computation
        parser.add_argument(
            '--typecomp',
            help='type of computation',
            type=str,
            choices=['full',
                     'dpre',
                     'roff'],
            required=True
        )

        # data file (only required for runoff)
        parser.add_argument(
            '--indata',
            help='file with prepared data',
            type=str
        )
        self.args = parser.parse_args()
        self.args.typecomp = CompType[self.args.typecomp]

        # load configuration
        self._config = ConfigParser()
        if self.args.typecomp == CompType.roff:
            if not self.args.indata:
                parser.error('--indata required')
            self._config.read(self.args.indata)

        # set logging level
        Logger.setLevel(self._config.get('Other', 'logging'))
        # sys.stderr logging
        self._add_logging_handler(
            logging.StreamHandler(stream=sys.stderr)
        )

        # must be defined for _cleanup() method
        Globals.outdir = self._config.get('Other', 'outdir')

    def load(self):
        """Load configuration data.

        Only roff procedure supported.
        """
        if self.args.typecomp == CompType.roff:
            # cleanup output directory first
            self._cleanup()

            data = self._load_roff(
                self._config.get('Other', 'indata')
            )

            self._set_globals(data)
        else:
            raise ProviderError('Unsupported partial computing: {}'.format(
                self.args.typecomp
            ))
