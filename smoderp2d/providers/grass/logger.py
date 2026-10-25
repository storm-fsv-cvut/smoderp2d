import os
import logging

from grass.script.core import info, error, warning, debug, percent
try:
    from qgis.core import Qgis, QgsMessageLog
except ImportError:
    # assume the user is using only GRASS and does not have QGIS installed
    pass

from smoderp2d.providers.logger import PROGRESS


class GrassGisLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the GRASS GIS."""

    def __init__(self):
        super(GrassGisLogHandler, self).__init__()

    def emit(self, record):
        """Write the log message.

        :param record: record to emit
        """
        if not record.msg:
            return

        os.environ['GRASS_VERBOSE'] = '1'  # show message

        if record.levelno >= PROGRESS:
            percent(record.msg, 100, 1)
            print()  # otherwise percent is not printed (TODO: why?)
        elif record.levelno >= logging.ERROR:
            error(record.msg)
        elif record.levelno >= logging.WARNING:
            warning(record.msg)
        elif record.levelno >= logging.INFO:
            info(record.msg)
        elif record.levelno >= logging.DEBUG:
            debug(record.msg)

        os.environ['GRASS_VERBOSE'] = '-1'  # hide module messages


class QGisLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the QGIS.
    """

    progress_reporter = None

    def __init__(self):
        super(QGisLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if not record.msg:
            return

        if record.levelno >= PROGRESS:
            self.progress_reporter(record.msg)
        elif record.levelno >= logging.ERROR:
            QgsMessageLog.logMessage(
                record.msg, 'SMODERP2D', level=Qgis.Critical
            )
        elif record.levelno >= logging.WARNING:
            QgsMessageLog.logMessage(
                record.msg, 'SMODERP2D', level=Qgis.Warning
            )
        elif record.levelno >= logging.INFO or record.levelno >= logging.DEBUG:
            # QGIS has no debug level
            QgsMessageLog.logMessage(record.msg, 'SMODERP2D', level=Qgis.Info)
