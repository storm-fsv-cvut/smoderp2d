import os
import sys
import subprocess
import tempfile
import binascii
import shutil

from smoderp2d.runners.base import Runner
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError

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
    def __init__(self):
        """Initialize runner.
        """
        self.grass_bin_path = self._find_grass_bin_path()
        if not os.getenv('GISRC'):
            self._set_environment()

        self._grass_session = None
        self._grass_session_crs = None
            
        super().__init__()
   
    @staticmethod
    def _find_grass_bin_path():
        """Find GRASS installation.
        :todo: Avoid bat file calling.
        """
        if sys.platform == 'win32':
            # MS Windows
            if 'QGIS_PREFIX_PATH' in os.environ:
                bin_path = os.path.join(os.environ['QGIS_PREFIX_PATH'],
                                        '..', '..',  'bin')
            else:
                bin_path = os.path.join(os.environ['OSGEO4W_ROOT'],
                                        'bin')
            grass_bin_path = None

            for grass_version in range(83, 89):
                gpath = os.path.join(bin_path, 'grass{}.bat'.format(grass_version))
                if os.path.exists(gpath):
                    grass_bin_path = gpath
                    break

            if grass_bin_path is None:
                raise ImportError("No GRASS executable found.")
        else:
            # expecting GNU/Linux
            grass_bin_path = shutil.which("grass")

        return grass_bin_path

    def finish(self):
        """Finish runner's operations.

        Close GRASS session."""
        from grass.script import setup as gsetup
        if self._grass_session:
            self._grass_session.finish()

        super().finish()
        
    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        return GrassGisProvider()

    @staticmethod
    def grass_version():
        """Get GRASS GIS version.

        :return list: GRASS version as a list (major, minor only)
        """
        # gs.version() requires g.gisenv which is not possible to use when no location is active
        # if list(map(int, gs.version()['version'].split('.')[:-1])) < [8, 3]:
        with open(os.path.join(os.environ["GISBASE"], "etc", "VERSIONNUMBER")) as fd:
            grass_version = fd.read().split(' ')[0]

        return list(map(int, grass_version.split('.')[:-1]))

    def _set_environment(self):
        """Set GRASS environment.

        :param str grass_bin_path: path to GRASS installation
        """
        startcmd = [self.grass_bin_path, '--config', 'path']

        p = Popen(startcmd,
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise ImportError("Reason: ({cmd}: {reason})".format(
                cmd=startcmd, reason=err)
            )

        str_out = out.decode("utf-8")
        gisbase = str_out.strip()

        # initialize GRASS runtime enviroment
        sys.path.append(os.path.join(gisbase, "etc", "python"))
        
        from grass.script.setup import setup_runtime_env
        setup_runtime_env(gisbase)

        # check version
        if self.grass_version() < [8, 3]:
            raise ProviderError("GRASS GIS version 8.3+ required")

    def create_location(self, epsg):
        """Create GRASS location.

        :param int epsg: EPSG code

        :return: grass_session object
        """
        from grass.script.setup import init
        from grass.pygrass.gis import Mapset
        
        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        os.makedirs(gisdb, exist_ok=True)

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

        # GISRC env variable must be set explicitly when run as batch
        # process (why?)
        import grass.lib.gis as libgis
        libgis.G_putenv("GISRC", os.environ["GISRC"])

        # calling gsetup.init() is not enough for PyGRASS (why?)
        Mapset('PERMANENT', location, gisdb).current()

        # update class properties
        self._grass_session = grass_session
        self._grass_session_crs = epsg

        return grass_session

    def import_data(self):
        """Import files to grass.
        """
        from grass.pygrass.modules import Module
        from grass.pygrass.gis import Mapset
        from osgeo import gdal, osr
        gdal.UseExceptions()
        # avoid GTIFF_SRS_SOURCE related warnings
        os.environ["GTIFF_SRS_SOURCE"] = "EPSG"

        if self.options is None:
            raise ProviderError("Provider options not set")

        Logger.info("Importing input data using GRASS GIS ({})...".format(
            Mapset().path())
        )

        for key, value in self.options.items():
            if not value:
                # skip optional options
                continue

            # import rasters
            if key == "elevation":
                ds = gdal.Open(value)
                proj = osr.SpatialReference(wkt=ds.GetProjection())
                crs = proj.GetAttrValue('AUTHORITY', 1)
                if crs is None or crs == self._grass_session_crs.split(':')[1]:
                    Module(
                        "r.import", input=value, output=key,
                        flags='o'
                    )
                else:
                    Module("r.import", input=value, output=key)
            # import vectors
            elif key in ("soil", "vegetation", "points", "streams"):
                Module(
                    "v.import", input=value, output=key, snap=0.001
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

        # update spatial data related options (path -> map name)
        for opt in ("elevation", "soil", "vegetation", "points", "streams",
                    "table_soil_vegetation", "channel_properties_table"):
            if self.options[opt]:
                self.options[opt] = opt

        Logger.info("Input data successully imported")
