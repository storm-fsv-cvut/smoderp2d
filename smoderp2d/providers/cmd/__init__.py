import sys
import argparse
if sys.version_info > (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

from smoderp2d.providers.base import BaseProvider, Logger

class CmdProvider(BaseProvider):
    def __init__(self):
        """Create argument parser."""
        super(CmdProvider, self).__init__()
        
        # define CLI parser
        self._parser = argparse.ArgumentParser(description='Run Smoderp2D.')

        # type of computation
        self._parser.add_argument(
            '--typecomp',
            help='type of computation',
            type=str,
            choices=['full',
                     'dpre',
                     'roff'],
            required=True
        )

        # data file (only required for runoff)
        self._parser.add_argument(
            '--indata',
            help='file with prepared data',
            type=str
        )
        self._args = self._parser.parse_args()

        # load configuration
        self._config = ConfigParser()
        if self._args.typecomp == 'roff':
            if not self._args.indata:
                self._parser.error('--indata required')
            self._config.read(self._args.indata)

        # set logging level
        Logger.setLevel(self._config.get('Other', 'logging'))
