import os
import sys

from smoderp2d.runners.grass import GrassGisRunner

class QGISRunner(GrassGisRunner):
    """Run SMODERP2D in QGIS environment."""
    def __init__(self, progress_reporter):
        """Initialize runner.

        :param progress_reporter: TODO
        """
        from qgis.core import QgsProject

        self.progress_reporter = progress_reporter
 
        try:
            super().__init__(self._find_grass_bin_path(),
                             create_location=QgsProject.instance().crs().authid())
        except ImportError as e:
            raise ImportError('Unable to find GRASS installation. {}'.format(e))

    @staticmethod
    def _find_grass_bin_path():
        """Find GRASS installation.
        :todo: Avoid bat file calling.
        """
        if sys.platform == 'win32':
            qgis_prefix_path = os.environ['QGIS_PREFIX_PATH']
            bin_path = os.path.join(qgis_prefix_path, '..', '..',  'bin')
            grass_bin_path = None

            for grass_version in range(83, 89):
                gpath = os.path.join(bin_path, 'grass{}.bat'.format(grass_version))
                if os.path.exists(gpath):
                    grass_bin_path = gpath
                    break

            if grass_bin_path is None:
                raise ImportError("No GRASS executable found.")
        else:
            grass_bin_path = '/usr/bin/grass'

        return grass_bin_path
        
    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        from smoderp2d.providers.grass.logger import QGisLogHandler
        
        QGisLogHandler.progress_reporter = self.progress_reporter
        return GrassGisProvider(QGisLogHandler)