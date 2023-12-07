import os
import sys
import logging
import subprocess
import tempfile
import shutil

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import BaseProvider, BaseWriter, WorkflowMode
from smoderp2d.providers.grass.logger import GrassGisLogHandler
from smoderp2d.providers import Logger

import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.raster import numpy2raster
from grass.pygrass.modules import Module as GrassModule

class Popen(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = si
        super().__init__(*args, **kwargs)

class Module:
    def __init__(self, *args, **kwargs):
        cmd = [shutil.which(args[0])]
        for p, v in kwargs.items():
            if p == 'overwrite' and v is True:
                cmd.append(f'--{p}')
            elif p == "flags":
                cmd.append(f"-{v}")
            else:
                cmd.append(f"{p}={v}")
        Logger.info(' '.join(cmd))
        tmp_fn = os.path.join(tempfile.gettempdir(), "cmd.bat") # TODO: better name
        genv = gs.gisenv()
        Logger.info(str(genv))
        gisdbase = genv['GISDBASE']
        location_name = genv['LOCATION_NAME']
        mapset = genv['MAPSET']
        with open(tmp_fn, "w") as tmp:
            tmp.write(f"chcp {self._getWindowsCodePage()}>NUL\n")
            #tmp.write(f'g.gisenv set="GISDBASE={gisdbase}"\n')
            #tmp.write(f'g.gisenv set="LOCATION_NAME={location_name}"\n')
            #tmp.write(f'g.gisenv set="MAPSET={mapset}"\n')
            tmp.write(' '.join(cmd))
        Popen(tmp_fn, shell=False, env=genv)
        #with Popen(tmp_fn, shell=False, stderr=subprocess.PIPE) as po:
        #    for line in iter(lambda: self._readline_with_recover(po.stderr), ''):
        #        Logger.info(str(line))

    @staticmethod
    def _readline_with_recover(stdout):
        try:
            return stdout.readline()
        except UnicodeDecodeError:
            return ''  # replaced-text

    @staticmethod
    def _getWindowsCodePage():
        """
        Determines MS-Windows CMD.exe shell codepage.
        Used into GRASS exec script under MS-Windows.
        """
        from ctypes import cdll
        return str(cdll.kernel32.GetACP())

class GrassGisWriter(BaseWriter):
    _vector_extension = '.gml'

    def __init__(self):
        super(GrassGisWriter, self).__init__()

        # primary key
        self.primary_key = "cat"

    def output_filepath(self, name, full_path=False):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :param full_path: True return full path otherwise only dataset name

        :return: full path to the dataset
        """
        if full_path:
            return BaseWriter.output_filepath(self, name)
        return name

    def _write_raster(self, array, file_output):
        """See base method for description.
        """
        self._check_globals()

        # set output region (use current region when GridGlobals are not set)
        if GridGlobals.r:
            region = Region()
            region.west = GridGlobals.xllcorner
            region.south = GridGlobals.yllcorner
            # TODO: use pygrass API instead
            region.east = region.west + (GridGlobals.c * GridGlobals.dx)
            region.north = region.south + (GridGlobals.r * GridGlobals.dy)
            region.cols = GridGlobals.c
            region.rows = GridGlobals.r
            region.write()

        raster_name = os.path.splitext(os.path.basename(file_output))[0]

        numpy2raster(
            array, "FCELL",
            raster_name, overwrite=True
        )

        self.export_raster(raster_name, file_output)

    def export_raster(self, raster_name, file_output):
        """Export GRASS raster map to output data format.

        :param raster_name: GRASS raster map name
        :param file_output: Target file path
        """
        Module(
            'r.out.gdal',
            input=raster_name,
            output=file_output + self._raster_extension,
            format='AAIGrid',
            nodata=GridGlobals.NoDataValue,
            type='Float64',
            overwrite=True,
        )

    def export_vector(self, raster_name, file_output):
        """Export GRASS vector map to output data format.

        :param raster_name: GRASS raster map name
        :param file_output: Target file path
        """
        Module(
            'v.out.ogr',
            input=raster_name,
            output=file_output + self._vector_extension,
            format='GML',
            overwrite=True,
        )


class GrassGisProvider(BaseProvider):

    def __init__(self, log_handler=GrassGisLogHandler):
        super(GrassGisProvider, self).__init__()

        # type of computation (default)
        self.args.workflow_mode = WorkflowMode.full

        # options must be defined by set_options()
        self._options = None

        # logger
        self.add_logging_handler(
            handler=log_handler(),
            formatter=logging.Formatter("%(message)s")
        )

        # check version
        # TBD: change to pygrass API
        if list(map(int, gs.version()['version'].split('.')[:-1])) < [8, 3]:
            raise ProviderError("GRASS GIS version 8.3+ required")

        # force overwrite
        os.environ['GRASS_OVERWRITE'] = '1'
        # be quiet
        os.environ['GRASS_VERBOSE'] = '0'

        # define storage writer
        self.storage = GrassGisWriter()

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._options = options

        # set output directory
        Globals.outdir = options['output']

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        if not self._options:
            raise ProviderError("No options given")

        from smoderp2d.providers.grass.data_preparation import PrepareData
        prep = PrepareData(self._options, self.storage)
        return prep.run()

    def _postprocessing(self):
        """See base method for description."""
        # here GRASS-specific postprocessing starts...
        Logger.debug('GRASS-specific postprocessing')
