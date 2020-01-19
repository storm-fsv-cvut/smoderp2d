import os
import sys
from zipfile import ZipFile

from pywps import Process, ComplexInput, ComplexOutput, Format

class Smoderp2d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input files (zip-archive)',
                         supported_formats=[Format('application/zip; charset=binary')])
        ]
        outputs = [
            ComplexOutput('output', 'Output ASCII raster data (zip-archive)',
                        supported_formats=[Format('application/zip')])
        ]

        super(Smoderp2d, self).__init__(
            self._handler,
            identifier='smoderp2d',
            version='0.1',
            title="Experimental SMODERP2D process",
            abstract='...',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        # lazy import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                        '..', '..', '..'))
        from smoderp2d import WpsRunner
        from smoderp2d.exceptions import ProviderError, ConfigError

        # input data (why .file is not working?
        input_zip = request.inputs['input'][0].data
        from io import BytesIO
        from zipfile import ZipFile
        from urllib.request import urlopen
        resp = urlopen(input_zip)
        with ZipFile(BytesIO(resp.read())) as zipfile:
            # print(zipfile.namelist())
            zipfile.extractall()

        # run computation
        runner = WpsRunner()
        runner.set_options({
            'typecomp': 'roff',
            'indata': 'tests/test.ini'
        })
        runner.run()

        # output data
        # response.outputs['output'].data = 'x'

        return response
