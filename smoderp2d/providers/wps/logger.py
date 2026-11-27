import logging
import time

from pywps import LOGGER

from smoderp2d.providers.logger import PROGRESS


class WpsLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the pyWPS.
    """
    def __init__(self, response):
        super(WpsLogHandler, self).__init__()
        self._response = response
        self._last_status = None

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if record.levelno >= PROGRESS:
            LOGGER.info("Progress value: {}%".format(record.msg))
            if self._last_status is None or time.time() - self._last_status > 5:
                # update status no more often than every 5 sec
                # (otherwise it will slow down the computation
                # significantly, see
                # https://github.com/storm-fsv-cvut/smoderp2d/issues/114)
                self._response.update_status(
                    message='Computation progress',
                    status_percentage=record.msg
                )
                self._last_status = time.time()
        elif record.levelno >= logging.ERROR:
            LOGGER.critical(record.msg)
        elif record.levelno >= logging.WARNING:
            LOGGER.warning(record.msg)
        elif record.levelno >= logging.INFO:
            LOGGER.info(record.msg)
        elif record.levelno >= logging.DEBUG:
            LOGGER.debug(record.msg)
