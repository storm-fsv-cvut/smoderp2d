import os
import sys


def start_smoderp2d():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from smoderp2d import Runner
    from smoderp2d.exceptions import ProviderError, ConfigError, \
        MaxIterationExceeded

    try:
        runner = Runner()
        sys.exit(runner.run())
    except (ConfigError, ProviderError, MaxIterationExceeded) as e:
        sys.exit('ERROR: {}'.format(e))
