#!/usr/bin/env python

"""
Resolves some input variables and start the computing

The computing itself is performed in src.runoff

.. todo::
 - main.py by se asi podle konvenci mel jmenovat smodepr.py
 - mal by tam byl setup.py
"""

from smoderp2d.providers import BaseProvider
    
def run():
    # initialize provider
    provider = BaseProvider()
    # load configuration (set global variables)
    provider.load()
    # print logo
    provider.logo()

    # must be called after initialization
    from smoderp2d.runoff import Runoff
    
    # the computation
    runoff = Runoff(provider)
    runoff.run()

if __name__ == "__main__":
    run()
