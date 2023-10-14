import os
import sys
import logging
from configparser import ConfigParser

from pywps import Process, ComplexInput, ComplexOutput, Format, LOGGER
from pywps.app.exceptions import ProcessError


class Profile1d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input profile CSV file',
                         supported_formats=[Format('text/csv')]),
            ComplexInput('soil_types', 'Input soil types CSV file',
                         supported_formats=[Format('text/csv')]),
            ComplexInput('rainfall', 'Input rainfall file',
                         supported_formats=[Format('text/plain')]),
            ComplexInput('config', 'Configuration INI file',
                         supported_formats=[Format('text/plain')])
        ]
        outputs = [
            ComplexOutput('profile', 'Output profile CSV file',
                          supported_formats=[Format('text/csv')],
                          as_reference=True),
            ComplexOutput('hydrograph', 'Output hydrograph CSV file',
                          supported_formats=[Format('text/csv')],
                          as_reference=True)
        ]

        super(Profile1d, self).__init__(
            self._handler,
            identifier='profile1d',
            version='0.1',
            title="Experimental PROFILE1D process",
            abstract="""Performs SMODERP distributed event-based model for surface and
subsurface runoff and erosion
(https://github.com/storm-fsv-cvut/smoderp2d) in 1D""",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def __update_config(self, input_, soil_types, rainfall, config):
        """Update configuration file."""
        config_parser = ConfigParser()
        config_parser.read(config)

        config_parser['data'] = {}
        config_parser['data']['rainfall'] = rainfall
        config_parser['data']['data1d'] = input_
        config_parser['data']['data1d_soil_types'] = soil_types
        config_parser['output'] = {}
        config_parser['output']['outdir'] = os.path.join(self.workdir, 'output')

        with open(config, 'w') as fd:
            config_parser.write(fd)

        return config

    @staticmethod
    def __set_response_output(response, output_dir, key, filename=None):
        """Set response output."""
        filepath = os.path.join(
            output_dir,
            '{}.csv'.format(key if filename is None else filename)
        )
        if not os.path.exists(filepath):
            raise ProcessError("Missing output - {}".format(filepath))
        else:
            response.outputs[key].file = filepath

    def _handler(self, request, response):
        sys.path.insert(0, "/opt/smoderp2d")

        from smoderp2d import WpsRunner
        from smoderp2d.exceptions import ProviderError, ConfigError, \
            MaxIterationExceeded
        from smoderp2d.core.general import Globals
        from smoderp2d.providers.wps.logger import WpsLogHandler

        config = self.__update_config(request.inputs['input'][0].file,
                                      request.inputs['soil_types'][0].file,
                                      request.inputs['rainfall'][0].file,
                                      request.inputs['config'][0].file)

        try:
            os.environ["SMODERP2D_PROFILE1D"] = "1"
            runner = WpsRunner(config_file=config)
            runner._provider.add_logging_handler(
                handler=WpsLogHandler(response),
                formatter=logging.Formatter("%(message)s")
            )

            runner.run()
        except (ConfigError, ProviderError, MaxIterationExceeded) as e:
            raise ProcessError("SMODERP failed: {}".format(e))

        # set response output
        LOGGER.info("Output data stored in: {}".format(Globals.get_outdir()))
        self.__set_response_output(response, Globals.get_outdir(), 'profile')
        self.__set_response_output(response, Globals.get_outdir(),
                                   'hydrograph', 'point001')
