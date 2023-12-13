import os
from smoderp2d.runners.base import Runner

class ArcGisRunner(Runner):
    """TODO."""

    def __init__(self):
        os.environ['ESRIACTIVEINSTALLATION'] = '1'
        super(ArcGisRunner, self).__init__()

    def _get_provider(self):
        from smoderp2d.providers.arcgis import ArcGisProvider
        return ArcGisProvider()
