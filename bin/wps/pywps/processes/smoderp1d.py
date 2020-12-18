import os
import sys
import fileinput
from configparser import ConfigParser

from pywps import Process, ComplexInput, ComplexOutput, Format, LOGGER
from pywps.app.exceptions import ProcessError

class Smoderp1d(Process):
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
            ComplexOutput('hydrogram', 'Output hydrogram CSV file',
                          supported_formats=[Format('text/csv')],
                          as_reference=True)
        ]

        super(Smoderp1d, self).__init__(
            self._handler,
            identifier='smoderp1d',
            version='0.1',
            title="Experimental SMODERP1D process",
            abstract="""Performs SMODERP2D distributed event-based model for surface and
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

        config_parser['rainfall'] = {}
        config_parser['rainfall']['file'] = rainfall
        config_parser['other'] = {}
        config_parser['other']['data1d'] = input_
        config_parser['other']['data1d_soil_types'] = soil_types
        config_parser['general'] = {}
        config_parser['general']['outdir'] = os.path.join(self.workdir, 'output')
        config_parser['general']['printtimes'] = '' # TODO
        config_parser['general']['logging'] = 'INFO' # TODO
        config_parser['general']['extraout'] = 'True'

        with open(config, 'w') as fd:
            config_parser.write(fd)

        return config

    @staticmethod
    def __set_response_output(response, output_dir, key):
        """Set response output."""
        filepath = os.path.join(output_dir,
                                '{}.csv'.format(key))
        if not os.path.exists(filepath):
            raise ProcessError("Missing output - {}".format(filepath))
        else:
            response.outputs[key].file = filepath

    def _handler(self, request, response):
        # TODO: report progress
        # for p in range(10, 101, 10):
        #     time.sleep(1)
        #     response.update_status(message='dummy computation', status_percentage=p)

        sys.path.insert(0, "/opt/smoderp2d")

        os.environ["NOGIS"] = "1"
        from smoderp2d import WpsRunner
        from smoderp2d.exceptions import ProviderError, ConfigError
        from smoderp2d.core.general import Globals

        config = self.__update_config(request.inputs['input'][0].file,
                                      request.inputs['soil_types'][0].file,
                                      request.inputs['rainfall'][0].file,
                                      request.inputs['config'][0].file)

        try:
            runner = WpsRunner(config_file=config)
            runner.run()
        except (ConfigError, ProviderError) as e:
            raise ProcessError("SMODERP failed: {}".format(e))

        # set response output
        LOGGER.info("Output data stored in: {}".format(Globals.get_outdir()))
        self.__set_response_output(response, Globals.get_outdir(), 'profile')
        # TODO
        # self.__set_response_output(response, Globals.get_outdir(), 'hydrogram')
