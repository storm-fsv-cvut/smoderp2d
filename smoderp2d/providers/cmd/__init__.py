import os
import sys
import argparse
import logging
import numpy as np

from smoderp2d.core.general import Globals
from smoderp2d.providers.base import BaseProvider, Logger, CompType, BaseWritter
from smoderp2d.exceptions import ConfigError

class CmdWritter(BaseWritter):
    def __init__(self):
        super(CmdWritter, self).__init__()

    def write_raster(self, array, output_name, directory='core'):
        """Write raster (numpy array) to ASCII file.

        :param array: numpy array
        :param output_name: output filename
        :param directory: directory where to write output file
        """
        file_output = self._raster_output_path(output_name, directory)

        np.savetxt(file_output, array, fmt='%.6e')

        self._print_array_stats(
            array, file_output
        )

class CmdArgumentParser(object):
    def __init__(self, config_file):
        self.config_file = config_file

    def set_config(self, description, typecomp=None):
        if self.config_file:
            return self.config_file, CompType()[typecomp]

        # define CLI parser
        parser = argparse.ArgumentParser(description)

        # type of computation
        if typecomp is None:
            parser.add_argument(
                '--typecomp',
                help='type of computation',
                type=str,
                choices=['full', 'dpre', 'roff'],
                required=True
            )

        # config file required
        parser.add_argument(
            '--config',
            help='file with configuration',
            type=str,
            required=True
        )

        args = parser.parse_args()

        if typecomp is None:
            return args.config, CompType()[args.typecomp]

        return args.config, CompType()[typecomp]

class CmdProvider(BaseProvider):
    def __init__(self, config_file=None):
        super(CmdProvider, self).__init__()

        # load configuration
        cloader = CmdArgumentParser(config_file)
        self.args.data_file, self.args.typecomp = cloader.set_config("Run SMODERP2D.")
        self._config = self._load_config()

        # define storage writter
        self.storage = CmdWritter()

    @staticmethod
    def __set_config_from_cli():
        parser = CmdArgumentParser('Run Smoderp2D.')

        self.args.typecomp = CompType()[parser.args.typecomp]

        # load configuration
        self._config = ConfigParser()
        if self.args.typecomp == CompType.roff:
            if not self.args.config:
                parser.error('--config required')
            if not os.path.exists(self.args.config):
                raise ConfigError("{} does not exist".format(
                    self.args.config
                ))
            self._config.read(self.args.config)

        try:
            # set logging level
            Logger.setLevel(self._config.get('other', 'logging'))
            # sys.stderr logging
            self._add_logging_handler(
                logging.StreamHandler(stream=sys.stderr)
            )

            # must be defined for _cleanup() method
            Globals.outdir = self._config.get('other', 'outdir')
        except NoSectionError as e:
            raise ConfigError('Config file {}: {}'.format(
                self.args.config, e
            ))

        # define storage writter
        self.storage = CmdWritter()

    def load(self):
        """Load configuration data.

        Only roff procedure supported.
        """
        if self.args.typecomp == CompType.roff:
            # cleanup output directory first
            self._cleanup()

            data = self._load_roff(
                self._config.get('other', 'config')
            )

            self._set_globals(data)
        else:
            raise ProviderError('Unsupported partial computing: {}'.format(
                self.args.typecomp
            ))
