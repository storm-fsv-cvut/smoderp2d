from pywps import Process, ComplexInput, ComplexOutput, Format

class Smoderp2d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input .save file',
                         supported_formats=[Format('application/zip')])
        ]
        outputs = [
            ComplexOutput('output', 'Output ASCII raster data',
                        supported_formats=[Format('application/zip')])
        ]

        super(Smoderp2d, self).__init__(
            self._handler,
            identifier='smoderp2d',
            version='0.1',
            title="Experimental SMODERP2D tool",
            abstract='...',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
            grass_location="epsg:5514"
        )

    def _handler(self, request, response):
        return response
