import logging

from smoderp2d.providers.logger import PROGRESS
from smoderp2d.exceptions import ProviderError

try:
    import arcpy
except RuntimeError as e:
    raise ProviderError("ArcGIS provider: {}".format(e))


class ArcPyLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the arcpy tool
    window.

    Taken from
    https://gis.stackexchange.com/questions/135920/logging-arcpy-error-messages
    """
    def __init__(self):
        super(ArcPyLogHandler, self).__init__()

    def emit(self, record):
        """Write the log message.

        :param record: record to emit
        """
        if record.levelno >= PROGRESS:
            arcpy.AddMessage("Progress value: {}%".format(record.msg))
        elif record.levelno >= logging.ERROR:
            arcpy.AddError(record.msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(record.msg)
        elif record.levelno >= logging.INFO:
            arcpy.AddMessage(record.msg)
