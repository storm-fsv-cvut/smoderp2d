#!/usr/bin/env python

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from smoderp2d import Runner
    from smoderp2d.exceptions import ProviderError

    try:
        runner = Runner()
        sys.exit(runner.run())
    except ProviderError as e:
        sys.exit('ERROR: {}'.format(e))
else:
    sys.exit("Can be run only as standalone program.")
