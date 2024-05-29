import os
import sys

from smoderp2d.runners.grass import GrassGisRunner

class QGISRunner(GrassGisRunner):
    """Run SMODERP2D in QGIS environment."""
    def __init__(self, progress_reporter):
        """Initialize runner.

        :param progress_reporter: TODO
        """
        self.progress_reporter = progress_reporter
 
        super().__init__()

    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        from smoderp2d.providers.grass.logger import QGisLogHandler
        
        QGisLogHandler.progress_reporter = self.progress_reporter
        return GrassGisProvider(QGisLogHandler)
