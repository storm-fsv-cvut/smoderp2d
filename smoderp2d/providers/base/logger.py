import os
import time

import logging
import logging.config

class BaseLogger(logging.Logger):
    def __init__(self, name):
        super(BaseLogger, self).__init__(name)
        self.startTime = time.time()


    def progress(self, i, dt, iter_, total_time):
        pass

def logger():
    """
    Return a logger.
    """
    #logging.config.fileConfig(
    #    os.path.join(os.path.dirname(__file__), 'logging.conf')
    #)

    logging.setLoggerClass(BaseLogger)
    logger = logging.getLogger('Smoderp')
    logger.setLevel(logging.DEBUG)

    return logger
