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
        self.info("Total time      [secs]: {0:.2f}".format(total_time)) # TODO: ms ???
        self.info("Time step       [secs]: {0:.2e}".format(dt))
        self.info("Time iterations       : {0:d}".format(iter_))
        self.info("Percentage done    [%]: {0:.2f}".format(i))
        units = ' [secs]'
        if i > 0:
            diff_time = time.time() - self.start_time
            remaining = (100.0 * diff_time) / i - diff_time
        else:
            remaining = '[??]'
        if (remaining > 60.) :
            remaining /= 60.
            units = ' [mins]'
        elif (remaining > (60.*60.)) :
            remaining /= (60.*60.)
            units = '[hours]'
        elif (remaining > (60.*60.*24.)) :
            remaining /= (60.*60.*24.)
            units = ' [days]'

        self.info("Time to end    {0}: {1:.2f}".format(units,remaining))
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
