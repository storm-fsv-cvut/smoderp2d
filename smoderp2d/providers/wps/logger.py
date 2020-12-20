class PyWpsLogHandler(logging.Handler):
    """Custom logging class that bounces messages to the pyWPS.
    """
    def __init__(self):
        super(PyWpsLogHandler, self).__init__()

    def emit(self, record):
        """ Write the log message.

        :param record: record to emit
        """
        if record.levelno >= PROGRESS_INFO:
            pass
        elif record.levelno >= logging.ERROR:
            fatal(record.msg)
        elif record.levelno >= logging.WARNING:
            warning(record.msg)
        elif record.levelno >= logging.INFO:
            info(record.msg)
        elif record.levelno >= logging.DEBUG:
            debug(record.msg)
