import os
import sys


def start_smoderp2d():
    from smoderp2d.runners.base import Runner
    from smoderp2d.exceptions import ProviderError, ConfigError, \
        MaxIterationExceeded

    try:
        runner = Runner()
        sys.exit(runner.run())
    except (ConfigError, ProviderError, MaxIterationExceeded) as e:
        sys.exit('ERROR: {}'.format(e))
