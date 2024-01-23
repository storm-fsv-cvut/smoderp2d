import os
import sys
import subprocess
import tempfile
import binascii

from smoderp2d.runners.grass import GrassGisRunner

class Popen(subprocess.Popen):
    """Avoid displaying cmd windows on MS Windows."""
    def __init__(self, *args, **kwargs):
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = si
        super().__init__(*args, **kwargs)

class QGISRunner(GrassGisRunner):
    """Run SMODERP2D in QGIS environment."""
    def __init__(self, progress_reporter, grass_bin_path='grass'):
        """Initialize runner.

        :param progress_reporter: TODO
        :param grass_bin_path: TODO
        """
        from grass.script import setup as gsetup
        from grass.pygrass.gis import Mapset
        from qgis.core import QgsProject

        self.progress_reporter = progress_reporter

        # create temp GRASS location
        epsg = QgsProject.instance().crs().authid()

        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        if not os.path.isdir(gisdb):
            os.mkdir(gisdb)

        # location: use random names for batch jobs
        string_length = 16
        location = binascii.hexlify(os.urandom(string_length)).decode("utf-8")

        p = Popen(
            [grass_bin_path, '-e', f'-c {epsg}', os.path.join(gisdb, location)]
        )
        p.wait()

        # # create location
        # try:
        #     gs.create_location(gisdb, location, epsg='5514', overwrite=True)
        # except SmoderpError as e:
        #     raise SmoderpError('{}'.format(e))

        # initialize GRASS session
        self._grass_session = gsetup.init(gisdb, location, 'PERMANENT')
        # calling gsetup.init() is not enough for PyGRASS
        Mapset('PERMANENT', location, gisdb).current()

        # test GRASS env varible
        if not os.getenv('GISRC'):
            raise SmoderpError('GRASS not found.')

        super().__init__()

    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        from smoderp2d.providers.grass.logger import QGisLogHandler
        
        QGisLogHandler.progress_reporter = self.progress_reporter
        return GrassGisProvider(QGisLogHandler)

    @staticmethod
    def import_data(options):
        """Import files to grass.

        :param options: dictionary of input data
        """
        from grass.pygrass.modules import Module

        for key in options:
            # import rasters
            if key == "elevation":
                from osgeo import gdal, osr
                from qgis.core import QgsProject

                ds = gdal.Open(options[key])
                proj = osr.SpatialReference(wkt=ds.GetProjection())
                srs = proj.GetAttrValue('AUTHORITY', 1)

                project_projection = QgsProject.instance().crs().authid()

                if srs is None or srs == project_projection.split(':')[1]:
                    Module(
                        "r.import", input=options[key], output=key,
                        flags='o'
                    )
                else:
                    Module("r.import", input=options[key], output=key)
            # import vectors
            elif key in ["soil", "vegetation", "points", "streams"]:
                if options[key] != '':
                    # points and streams are optional
                    Module(
                        "v.import", input=options[key], output=key
                    )
            # import tables
            elif key in ["table_soil_vegetation",
                         "channel_properties_table"]:
                if options[key] != '':
                    # channel_properties_table is optional
                    from osgeo import ogr
                    kwargs = {}
                    ds = ogr.Open(options[key])
                    if ds:
                        if ds.GetDriver().GetName() == 'CSV':
                            kwargs['gdal_doo'] = 'AUTODETECT_TYPE=YES'
                        ds = None
                    Module(
                        "db.in.ogr", input=options[key], output=key,
                        **kwargs
                    )

    def finish(self):
        """TODO."""
        from grass.script import setup as gsetup
        self._grass_session.finish()
