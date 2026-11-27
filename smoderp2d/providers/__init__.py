# from smoderp2d.providers.base import BaseProvider

import os
import logging
import time


def logger():
    """Return a logger."""
    from smoderp2d.providers.logger import BaseLogger

    logging.setLoggerClass(BaseLogger)
    logger_name = 'SMODERP2D'
    if os.getenv('ESRIACTIVEINSTALLATION'):
        # create unique logger for each run (see ArcGIS issue #22)
        logger_name += '_{}'.format(time.time())

    return logging.getLogger(logger_name)


Logger = logger()
