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

def run():
    # initialize provider
    if os.getenv('ESRIACTIVEINSTALLATION'):
        from smoderp2d.providers.arcgis import ArcGisProvider
        provider_class = ArcGisProvider
    elif os.getenv('GISRC'):
        from smoderp2d.providers.grass import GrassProvider
        provider_class = GrassProvider
    else:
        from smoderp2d.providers.cmd import CmdProvider
        provider_class = CmdProvider
    provider = provider_class()

    # print logo
    provider.logo()

    # load configuration (set global variables)
    provider.load()

    # must be called after initialization (!)
    from smoderp2d.runoff import Runoff

    # the computation
    runoff = Runoff(provider)
    runoff.run()

    return 0
