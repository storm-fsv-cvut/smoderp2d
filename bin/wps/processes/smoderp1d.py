from pywps import Process, ComplexInput, ComplexOutput, Format

class Smoderp1d(Process):
    def __init__(self):
        inputs = [
            ComplexInput('input', 'Input profile CSV file',
                         supported_formats=[Format('text/csv')]),
            ComplexInput('soil_types', 'Input soil types CSV file',
                         supported_formats=[Format('text/csv')])
        ]
        outputs = [
            ComplexOutput('output', 'Output CSV file',
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
            outputs=outputs, store_supported=True, status_supported=True
        )

    def _handler(self, request, response):
        response.outputs['output'].file = request.inputs['input'][0].file
