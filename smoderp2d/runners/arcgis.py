import os
from smoderp2d.runners.base import Runner

class ArcGisRunner(Runner):
    """Run SMODERP2D in ArcGIS environment."""
    def __init__(self):
        os.environ['ESRIACTIVEINSTALLATION'] = '1'
        super(ArcGisRunner, self).__init__()

    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.arcgis import ArcGisProvider
        return ArcGisProvider()
