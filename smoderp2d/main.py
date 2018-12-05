#!/usr/bin/env python

"""
Resolves some input variables and start the computing

The computing itself is performed in src.runoff


.. todo::
 - main.py by se asi podle konvenci mel jmenovat smodepr.py
 - mal by tam byl setup.py
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

    # must be called after initialization
    from smoderp2d.runoff import Runoff
    
    # the computation
    runoff = Runoff(provider)
    runoff.run()

if __name__ == "__main__":
    run()
