# from smoderp2d.providers.base import BaseProvider

import os
import time

import logging
import logging.config

class BaseLogger(logging.Logger):
    def __init__(self, name):
        super(BaseLogger, self).__init__(name)
        self.start_time = time.time()

    def progress(self, i, dt, iter_, total_time):
        self.info("Total time      [s]: {0:.2f}".format(total_time)) # TODO: ms ???
        self.info("Time step       [s]: {0:.2f}".format(dt))
        self.info("Time iterations    : {0:d}".format(iter_))
        self.info("Percentage done [%]: {0:.2f}".format(i))
        if i > 0:
            diff_time = time.time() - self.start_time
            remaining = (100.0 * diff_time) / i - diff_time
        else:
            remaining = '??'
        self.info("Time to end     [s]: {0:.2f}".format(remaining))
        self.info('-' * 80)

def logger():
    """
    Return a logger.
    """
    logging.setLoggerClass(BaseLogger)
    logger_name = 'SMODERP2D'
    if os.getenv('ESRIACTIVEINSTALLATION'):
        # create unique logger for each run (see ArcGIS issue #22)
        logger_name += '_{}'.format(time.time())
    logger = logging.getLogger(logger_name)

    return logger

Logger = logger()
