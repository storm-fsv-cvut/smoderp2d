#!/usr/bin/env python3

"""
Starting the rainfall/runoff/soil loss model
SMODERP2D.

Help:
    ./bin/start-profile1d.py --config tests/profile1d.ini
"""
import os
from start import start_smoderp2d

if __name__ == "__main__":
    os.environ["SMODERP2D_PROFILE1D"] = "1"
    start_smoderp2d()
else:
    sys.exit("Can be run only as standalone program.")
