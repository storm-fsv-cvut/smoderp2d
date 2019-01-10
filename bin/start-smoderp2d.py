#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from smoderp2d import run
    from smoderp2d.exceptions import ProviderError

    try:
        sys.exit(run())
    except ProviderError as e:
        sys.exit(e)
else:
    sys.exit("Can be run only as standalone program.")
