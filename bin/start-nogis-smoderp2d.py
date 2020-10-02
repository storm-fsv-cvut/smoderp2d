#!/usr/bin/env python

"""
Starting the rainfall/runoff/soil loss model 
SMODERP2D.

Help:
    ./bin/start-nogis-smoderp2d.py -cfg tests/nogis.ini
"""
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    # set new environmental variable for provider factory in
    # smoderp2d.__init__.py
    os.environ["NOGIS"] = "1"
    from smoderp2d import Runner
    from smoderp2d.exceptions import ProviderError, ConfigError

    try:
        runner = Runner()
        sys.exit(runner.run())
    except (ConfigError, ProviderError) as e:
        sys.exit('ERROR: {}'.format(e))
else:
    sys.exit("Can be run only as standalone program.")
