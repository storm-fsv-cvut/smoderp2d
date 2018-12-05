import logging

import arcpy

class ArcPyLogHandler(logging.Handler):
    """
    Custom logging class that bounces messages to the arcpy tool window as well
    as reflecting back to the file.

    Taken from https://gis.stackexchange.com/questions/135920/logging-arcpy-error-messages
    """
    def __init__(self):
        super(ArcPyLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        try:
            msg = record.msg.format(record.args)
        except:
            msg = record.msg

        if record.levelno >= logging.ERROR:
            arcpy.AddError(msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(msg)
        elif record.levelno >= logging.INFO:
            arcpy.AddMessage(msg)
