import os
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from pywps import Process, ComplexInput, ComplexOutput, Format

class Smoderp2d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input files (zip-archive)',
                         supported_formats=[Format('application/zip; charset=binary')])
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
    def process_input(input_zip):
        # input data (why .file is not working?
        from io import BytesIO
        from urllib.request import urlopen
        resp = urlopen(input_zip)
        with ZipFile(BytesIO(resp.read())) as zipfile:
            zipfile.extractall()
            for f in zipfile.namelist():
                if os.path.splitext(f)[1] == '.ini':
                    indata = f

        return indata

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

    def _handler(self, request, response):
        # lazy import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        '..', '..', '..'))
        from smoderp2d import WpsRunner
        from smoderp2d.exceptions import ProviderError, ConfigError
        from smoderp2d.core.general import Globals

        # input data
        indata = self.process_input(request.inputs['input'][0].data)
        if not indata:
            raise Exception("Input ini file not found")

        # run computation
        runner = WpsRunner()
        runner.set_options({
            'typecomp': 'roff',
            'indata': indata
        })
        runner.run()

        # output data
        response.outputs['output'].file = self.process_output(Globals.get_outdir())

        return response
