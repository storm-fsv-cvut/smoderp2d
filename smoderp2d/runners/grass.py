import os
import sys
import subprocess
import tempfile
import binascii

from smoderp2d.runners.base import Runner
from smoderp2d.providers import Logger

class Popen(subprocess.Popen):
    """Avoid displaying cmd windows on MS Windows."""
    def __init__(self, *args, **kwargs):
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = si
        super().__init__(*args, **kwargs)

class GrassGisRunner(Runner):
    """Run SMODERP2D in GRASS GIS environment."""
    def __init__(self, grass_bin_path='/usr/bin/grass', create_location=None):
        """Initialize runner.

        :param str grass_bin_path: path to GRASS installation directory
        :param str create_location: EPSG code to create new location
        """
        self.grass_bin_path = None
        if not os.getenv('GISRC'):
            self._set_environment(grass_bin_path)
        if create_location:
            self._crs = create_location
            self._grass_session = self._create_location(self._crs)
        else:
            self._grass_session = None
            self._crs = None # TODO
            
        super().__init__()
   
        # test GRASS env varible
        if not os.getenv('GISRC'):
            raise SmoderpError('GRASS not found.')


    def finish(self):
        """Close GRASS session."""
        from grass.script import setup as gsetup
        if self._grass_session:
            self._grass_session.finish()
        
    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        return GrassGisProvider()

    def _set_environment(self, grass_bin_path):
        """Set GRASS environment.

        :param str grass_bin_path: path to GRASS installation
        """
        if self.grass_bin_path is not None:
            # avoid reestablishment of the environment
            return

        self.grass_bin_path = grass_bin_path        
        startcmd = [self.grass_bin_path, '--config', 'path']

        p = Popen(startcmd,
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise ImportError("Reason: ({cmd}: {reason})".format(
                cmd=startcmd, reason=err)
            )

        str_out = out.decode("utf-8")
        gisbase = str_out.rstrip(os.linesep)

        # Initialize GRASS runtime enviroment
        sys.path.append(os.path.join(gisbase, "etc", "python"))
        
        from grass.script.setup import setup_runtime_env
        setup_runtime_env(gisbase)

    def _create_location(self, epsg):
        """Create GRASS location.

        :param int epsg: EPSG code

        :return: grass_session object
        """
        from grass.script.setup import init
        from grass.pygrass.gis import Mapset
        
        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        if not os.path.isdir(gisdb):
            os.mkdir(gisdb)

        # location: use random names for batch jobs
        string_length = 16
        location = binascii.hexlify(os.urandom(string_length)).decode("utf-8")

        p = Popen(
            [self.grass_bin_path, '-e', f'-c {epsg}', os.path.join(gisdb, location)]
        )
        p.wait()

        # # create location
        # try:
        #     gs.create_location(gisdb, location, epsg='5514', overwrite=True)
        # except SmoderpError as e:
        #     raise SmoderpError('{}'.format(e))

        # initialize GRASS session
        grass_session = init(gisdb, location, 'PERMANENT')
        print(gisdb, location)
        # calling gsetup.init() is not enough for PyGRASS
        Mapset('PERMANENT', location, gisdb).current()

        return grass_session
    
    def import_data(self, options):
        """Import files to grass.

        :param options: dictionary of input data
        """
        from grass.pygrass.modules import Module
        from grass.pygrass.gis import Mapset

        Logger.debug("Using GRASS location: {}".format(
            Mapset().path())
        )

        for key, value in options.items():
            if not value:
                # skip optional options
                continue

            # import rasters
            if key == "elevation":
                from osgeo import gdal, osr

                ds = gdal.Open(value)
                proj = osr.SpatialReference(wkt=ds.GetProjection())
                crs = proj.GetAttrValue('AUTHORITY', 1)
                if crs is None or crs == self._crs.split(':')[1]:
                    Module(
                        "r.import", input=value, output=key,
                        flags='o'
                    )
                else:
                    Module("r.import", input=value, output=key)
            # import vectors
            elif key in ("soil", "vegetation", "points", "streams"):
                Module(
                    "v.import", input=value, output=key
                )
            # import tables
            elif key in ("table_soil_vegetation",
                         "channel_properties_table"):
                # channel_properties_table is optional
                from osgeo import ogr
                kwargs = {}
                ds = ogr.Open(value)
                if ds:
                    if ds.GetDriver().GetName() == 'CSV':
                        kwargs['gdal_doo'] = 'AUTODETECT_TYPE=YES'
                    ds = None
                Module(
                    "db.in.ogr", input=value, output=key,
                    **kwargs
                )

        # TODO: it must be set also for QGIS somehow (?)
        for opt in ("elevation", "soil", "vegetation", "points", "streams",
                    "table_soil_vegetation", "channel_properties_table"):
            if options[opt]:
                options[opt] = opt
