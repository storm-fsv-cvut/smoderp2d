import sys
import argparse
if sys.version_info > (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider, Logger

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
        self._args = parser.parse_args()

        # load configuration
        self._config = ConfigParser()
        if self._args.typecomp == 'roff':
            if not self._args.indata:
                parser.error('--indata required')
            self._config.read(self._args.indata)

        # set logging level
        Logger.setLevel(self._config.get('Other', 'logging'))

        # must be defined for _cleanup() method
        Globals.outdir = self._config.get('Other', 'outdir')

    def load(self):
        """Load configuration data.

        Only roff procedure supported.
        """
        if self._args.typecomp == 'roff':
            # cleanup output directory first
            self._cleanup()

            data = self._load_roff(
                self._config.get('Other', 'indata')
            )

            self._set_globals(data)
        else:
            raise ProviderError('Unsupported partial computing: {}'.format(
                self._args.typecomp
            ))
