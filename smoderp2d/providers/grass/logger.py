import os
import logging

from grass.script.core import info, error, warning, debug, percent

from smoderp2d.providers.logger import PROGRESS

class GrassGisLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the GRASS GIS.
    """
    def __init__(self):
        super(GrassGisLogHandler, self).__init__()
        # TODO: use Messenger
        # self._msg = Messenger()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        os.environ['GRASS_VERBOSE'] = '1' # show message

        if record.levelno >= PROGRESS:
            percent(record.msg, 100, 1)
            print() # otherwise percent is not printed (TODO: why?)
        elif record.levelno >= logging.ERROR:
            error(record.msg)
        elif record.levelno >= logging.WARNING:
            warning(record.msg)
        elif record.levelno >= logging.INFO:
            info(record.msg)
        elif record.levelno >= logging.DEBUG:
            debug(record.msg)

        os.environ['GRASS_VERBOSE'] = '-1' # hide module messages
