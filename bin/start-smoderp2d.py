#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    import smoderp2d.main as sm

    sm.run()
else:
    sys.exit("Can be run only as standalone program.")
