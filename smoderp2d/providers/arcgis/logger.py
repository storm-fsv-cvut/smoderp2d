import logging

import arcpy

class ArcPyLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the arcpy tool
    window.

    Taken from
    https://gis.stackexchange.com/questions/135920/logging-arcpy-error-messages
    """
    def __init__(self):
        super(ArcPyLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if record.levelno >= logging.ERROR:
            arcpy.AddError(record.msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(record.msg)
        elif record.levelno >= logging.INFO:
            arcpy.AddMessage(record.msg)
