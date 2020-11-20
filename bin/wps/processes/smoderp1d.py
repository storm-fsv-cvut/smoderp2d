import time

from pywps import Process, ComplexInput, ComplexOutput, Format

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

    def _handler(self, request, response):
        # dummy computation
        for p in range(10, 101, 10):
            time.sleep(1)
            response.update_status(message='dummy computation', status_percentage=p)

        response.outputs['profile'].file = 'processes/profile.csv'
        response.outputs['hydrogram'].file = 'processes/hydrogram.csv'
