# TODO: not tested yet

from base import BaseProvider

class GrassProvider(BaseProvider):
    from grass.pygrass.messages import Messenger
    
    def __init__(self):
        self._msgr = Messenger()

    def message(self, line):
        """Print string.

        :param str line: string to be printed
        """
        self._msgr.message(line)
