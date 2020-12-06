import os
import sys

from pywps import Process, ComplexInput, ComplexOutput, Format, LOGGER

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

    @staticmethod
    def __update_config(input_, soil_types, rainfall, config):
        # TODO
        return config

    def _handler(self, request, response):
        # dummy computation
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
            # TODO
            pass

        LOGGER.info("Output data stored in: {}".format(Globals.get_outdir()))
        response.outputs['profile'].file = os.path.join(Globals.get_outdir(),
                                                        'profile.csv')
        response.outputs['hydrogram'].file = os.path.join(Globals.get_outdir(),
                                                          'hydrogram.csv')
