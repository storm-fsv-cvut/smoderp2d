import logging

from grass.script.core import fatal, warning, message

class GrassGisLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the GRASS GIS.
    """
    def __init__(self):
        super(GrassGisLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if record.levelno >= logging.ERROR:
            fatal(record.msg)
        elif record.levelno >= logging.WARNING:
            warning(record.msg)
        elif record.levelno >= logging.INFO:
            message(record.msg)
        elif record.levelno >= logging.INFO:
            debug(record.msg)
