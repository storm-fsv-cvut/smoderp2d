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
    def set_options(self, options):
        self._provider.set_options(options)
