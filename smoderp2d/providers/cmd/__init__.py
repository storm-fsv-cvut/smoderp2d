import os
import argparse
import numpy as np

from smoderp2d.core.general import GridGlobals
from smoderp2d.providers.base import BaseProvider, BaseWriter, WorkflowMode
from smoderp2d.exceptions import ConfigError


class CmdWriter(BaseWriter):
    def __init__(self):
        super(CmdWriter, self).__init__()

    def _write_raster(self, array, file_output):
        """See base method for description.
        """
        header = f'ncols\t{GridGlobals.c}\nnrows\t{GridGlobals.r}\n' \
                 f'xllcorner\t{GridGlobals.xllcorner}\n' \
                 f'yllcorner\t{GridGlobals.yllcorner}\n' \
                 f'cellsize\t{np.sqrt(GridGlobals.pixel_area)}\n' \
                 f'NODATA_value\t{GridGlobals.NoDataValue}'

        np.savetxt(
            file_output + self._raster_extension, array, fmt='%.6e',
            header=header, comments=''
        )


class CmdArgumentParser(object):
    def __init__(self, config_file):
        self.config_file = config_file

    def set_config(self, description, workflow_mode):
        if self.config_file:
            return self.config_file, WorkflowMode()['roff']

        # define CLI parser
        parser = argparse.ArgumentParser(description)

        # config file required
        parser.add_argument(
            '--config',
            help='file with configuration',
            type=str,
            required=True
        )

        args = parser.parse_args()

        return args.config, WorkflowMode()[workflow_mode]


class CmdProvider(BaseProvider):
    def __init__(self, config_file=None):
        super(CmdProvider, self).__init__()

        # load configuration
        if config_file is None and os.getenv("SMODERP2D_CONFIG_FILE"):
            config_file = os.getenv("SMODERP2D_CONFIG_FILE")
        cloader = CmdArgumentParser(config_file)
        self.args.config_file, self.args.workflow_mode = cloader.set_config(
            "Run SMODERP2D.", workflow_mode='roff')
        self._config = self._load_config()
        try:
            self.args.data_file = self._config.get('data', 'pickle')
        except KeyError:
            raise ConfigError("No pickle defined")

        # define storage writer
        self.storage = CmdWriter()
