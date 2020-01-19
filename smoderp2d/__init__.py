"""
Documentation of Smoderp, distributed event-based model for surface and subsurface runoff and erosion.

.. moduleauthor:: Petr Kavka, Karel Vrana and Jakum Jerabek
                  model was bild in cooperation with eng. students (Jan Zajicek, Nikola Nemcova, Tomas Edlman, Martin Neumann)

The computational options are as follows:
 - Type of flow
  - surface
   - subsurface
   - surface + subsurface
 - Flow direction algorithm
   - D8 (default)
   - multi-flow direction
 - Erosion
   - none
   - sheet erosion
   - sheet erosion + rill erosion
 - Stream
   - yes
   - no
"""

import os

from smoderp2d.providers.base import CompType
from .providers.base.exceptions import DataPreparationInvalidInput
from .exceptions import SmoderpError

class Runner(object):
    def __init__(self):
        self._provider = self._provider_factory()

    def _provider_factory(self):
        # initialize provider
        if os.getenv('ESRIACTIVEINSTALLATION'):
            from smoderp2d.providers.arcgis import ArcGisProvider
            provider_class = ArcGisProvider
        elif os.getenv('GISRC'):
            from smoderp2d.providers.grass import GrassGisProvider
            provider_class = GrassGisProvider
        elif isinstance(self, WpsRunner):
            from smoderp2d.providers.wps import WpsProvider
            provider_class = WpsProvider
        else:
            from smoderp2d.providers.cmd import CmdProvider
            provider_class = CmdProvider
        provider = provider_class()

        return provider

    def set_comptype(self, comp_type, data_file=None):
        """Set computation type.

        :param CompType comp_type: computation type
        :param str data_file: data file (input/output)
        """
        if comp_type in (CompType.dpre, CompType.roff) and not data_file:
            raise SmoderpError("Data file not defined")
        self._provider.args.typecomp = comp_type
        self._provider.args.data_file = data_file

    def run(self):
        # print logo
        self._provider.logo()

        # load configuration (set global variables)
        try:
            self._provider.load()
        except DataPreparationInvalidInput:
            return 1

        if self._provider.args.typecomp == CompType.dpre:
            # data prepararation only requested
            return

        # must be called after initialization (!)
        from smoderp2d.runoff import Runoff
        # the computation
        runoff = Runoff(self._provider)
        runoff.run()

        return 0


class GrassRunner(Runner):
    def set_options(self, options):
        self._provider.set_options(options)


class QGISRunner(GrassRunner):
    def __init__(self):

        # create temp GRASS location
        import tempfile
        import binascii
        import grass.script as gs
        from grass.script import setup as gsetup

        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        if not os.path.isdir(gisdb):
            os.mkdir(gisdb)

        # location: use random names for batch jobs
        string_length = 16
        location = binascii.hexlify(os.urandom(string_length)).decode("utf-8")

        # initialize GRASS session
        gsetup.init(os.environ['GISBASE'], gisdb, location, 'PERMANENT')

        # create location
        try:
            gs.create_location(gisdb, location, epsg='5514', overwrite=True)
        except SmoderpError as e:
            raise SmoderpError('{}'.format(e))

        # test GRASS env varible
        if not os.getenv('GISRC'):
            raise SmoderpError('GRASS not found.')

        super().__init__()

    def import_data(self, options):
        """
        Import files to grass

        :param options: dictionary of input data
        """
        from grass.pygrass.modules import Module

        for key in options:
            try:
                # import rasters
                if key == "elevation":
                    Module("r.import", input=options[key], output=key)
                # import vectors
                elif key in ["soil", "vegetation", "points", "stream"]:
                    Module("v.import", input=options[key], output=key, flags = 'o')
                # import tables
                elif key in ["table_soil_vegetation", "table_stream_shape"]:
                    Module("db.in.ogr", input=options[key], output=key)
            except SmoderpError as e:
                raise SmoderpError('{}'.format(e))

    def export_data(self):
        pass

    def __del__(self):
        pass

class WpsRunner(Runner):
    def set_options(self, options):
        self._provider.set_options(options)
