#!/usr/bin/env python3

"""
Starting the rainfall/runoff/soil loss model
SMODERP2D.

Help:
    ./bin/start-smoderp2d.py --config tests/quicktest.ini
"""

import sys
from start import start_smoderp2d

if __name__ == "__main__":
    start_smoderp2d()
else:
    sys.exit("Can be run only as standalone program.")
