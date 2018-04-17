import sys
import types
import logging
import os

# python 2.7 hack (in Python 3 can be replaced by 'terminates')
def customEmit(self, record):
    try:
        msg = self.format(record)
        if not hasattr(types, "UnicodeType"): # if no unicode support...
            self.stream.write(msg)
        else:
            try:
                if getattr(self.stream, 'encoding', None) is not None:
                    self.stream.write(msg.encode(self.stream.encoding))
                else:
                    self.stream.write(msg)
            except UnicodeError:
                self.stream.write(msg.encode("UTF-8"))
        self.flush()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        self.handleError(record)

class NoNewLineLogHandler(logging.StreamHandler):
    def __init__(self, *args):
        setattr(logging.StreamHandler,
                logging.StreamHandler.emit.__name__,
                customEmit
        )
        logging.StreamHandler.__init__(self, *args)
        

class LoggerClass(logging.getLoggerClass()):
    def __init__(self, name, level=logging.NOTSET):
        self.name = name
        super(LoggerClass, self).__init__(name)
        self.addHandler(NoNewLineLogHandler(sys.stderr))
        self.setLevel(level)

    def debug(self, message, *args, **kwargs):
        if not self.isEnabledFor(logging.DEBUG):
            return
        self._log(logging.DEBUG, '[{}][DEBUG]: {}{}'.format(self.name,
                                                            message,
                                                            os.linesep),
                  args, **kwargs
        )

    def info(self, message, *args, **kwargs):
        if not self.isEnabledFor(logging.INFO):
            return
        self._log(logging.INFO, '[{}][INFO]: {}{}'.format(self.name,
                                                          message,
                                                          os.linesep),
                  args, **kwargs
        )

    def warning(self, message, *args, **kwargs):
        if not self.isEnabledFor(logging.WARNING):
            return
        self._log(logging.WARNING, '[{}][WARNING]: {}{}'.format(self.name,
                                                                message,
                                                                os.linesep),
                  args, **kwargs
        )

    def error(self, message, *args, **kwargs):
        if not self.isEnabledFor(logging.ERROR):
            return
        self._log(logging.ERROR, '[{}][ERROR]: {}{}'.format(self.name,
                                                            message,
                                                            os.linesep),
                  args, **kwargs
        )

    def critical(self, message, *args, **kwargs):
        if not self.isEnabledFor(logging.CRITICAL):
            return
        self._log(logging.CRITICAL, '[{}][CRITICAL]: {}{}'.format(self.name,
                                                                  message,
                                                                  os.linesep),
                  args, **kwargs
        )

Logger = LoggerClass('Smoderp')
