import os
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from pywps import Process, ComplexInput, ComplexOutput, Format

class Smoderp2d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input SAVE file',
                         supported_formats=[Format('text/plain')]),
            ComplexInput('rainfall', 'Input rainfall file',
                         supported_formats=[Format('text/plain')]),
            ComplexInput('config', 'Configuration INI file',
                         supported_formats=[Format('text/plain')])
        ]
        outputs = [
            ComplexOutput('output', 'Output ASCII raster data (zip-archive)',
                          supported_formats=[Format('application/zip')],
                          as_reference=True)
        ]

        super(Smoderp2d, self).__init__(
            self._handler,
            identifier='smoderp2d',
            version='0.1',
            title="Experimental SMODERP2D process",
            abstract="Performs SMODERP2D distributed event-based model for surface and subsurface runoff and erosion (https://github.com/storm-fsv-cvut/smoderp2d)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    @staticmethod
    def process_output(outdir):
        def zipdir(path, ziph):
            # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    ziph.write(os.path.join(root, file))

        outfile = 'output.zip'
        with ZipFile(outfile, 'w', ZIP_DEFLATED) as fd:
            zipdir(outdir, fd)

        return outfile

    def __update_config(self, input_, rainfall, config):
        """Update configuration file."""
        config_parser = ConfigParser()
        config_parser.read(config)

        config_parser['rainfall'] = {}
        config_parser['rainfall']['file'] = rainfall
        config_parser['other'] = {}
        config_parser['other']['config'] = input_
        config_parser['general'] = {}
        config_parser['general']['outdir'] = os.path.join(self.workdir, 'output')

        with open(config, 'w') as fd:
            config_parser.write(fd)

        return config
    
    def _handler(self, request, response):
        sys.path.insert(0, "/opt/smoderp2d")
        from smoderp2d import WpsRunner
        from smoderp2d.exceptions import ProviderError, ConfigError
        from smoderp2d.core.general import Globals

        config = self.__update_config(request.inputs['input'][0].file,
                                      request.inputs['rainfall'][0].file,
                                      request.inputs['config'][0].file)

        try:
            runner = WpsRunner(config_file=config)
            runner.run()
        except (ConfigError, ProviderError) as e:
            raise ProcessError("SMODERP failed: {}".format(e))

        # output data
        response.outputs['output'].file = self.process_output(Globals.get_outdir())
