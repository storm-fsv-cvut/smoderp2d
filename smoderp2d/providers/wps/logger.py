import logging

from pywps import LOGGER

from smoderp2d.providers import PROGRESS_INFO

class WpsLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the pyWPS.
    """
    def __init__(self):
        super(WpsLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if record.levelno >= PROGRESS_INFO:
            LOGGER.info("Progress value: {}%".format(record.msg))
        elif record.levelno >= logging.ERROR:
            LOGGER.critical(record.msg)
        elif record.levelno >= logging.WARNING:
            LOGGER.warning(record.msg)
        elif record.levelno >= logging.INFO:
            LOGGER.info(record.msg)
        elif record.levelno >= logging.DEBUG:
            LOGGER.debug(record.msg)
