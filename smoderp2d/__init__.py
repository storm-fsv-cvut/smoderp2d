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
from smoderp2d.exceptions import SmoderpError


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
        else:
            from smoderp2d.providers.cmd import CmdProvider
            provider_class = CmdProvider
        provider = provider_class()

        return provider

    def run(self):
        # print logo
        self._provider.logo()

        # load configuration (set global variables)
        self._provider.load()

        # must be called after initialization (!)
        from smoderp2d.runoff import Runoff

        # the computation
        runoff = Runoff(self._provider)
        runoff.run()

        return 0


class GrassRunner(Runner):
    def set_options(self):
        self._provider.set_options(options)


class QGISRunner(GrassRunner):
    def __init__(self):

        # create temp GRASS location
        import tempfile
        import binascii
        import grass.script as gs

        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        if not os.path.isdir(gisdb):
            os.mkdir(gisdb)

        # location: use random names for batch jobs
        string_length = 16
        location = binascii.hexlify(os.urandom(string_length))

        # initialize GRASS session
        gs.setup.init(os.environ['GISBASE'], gisdb, location, 'PERMANENT')

        # create location
        try:
            gs.create_location(gisdb, location, epsg='5514', overwrite=True)
        except SmoderpError as e:
            raise SmoderpError('{}'.format(e))

        super().__init__()

    def _import_data(self):
        pass

    def _export_data(self):
        pass

    def __del__(self):
        pass
