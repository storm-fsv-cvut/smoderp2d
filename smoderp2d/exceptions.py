class SmoderpError(Exception):
    pass

class ProviderError(Exception):
    def __init__(self, msg):
        Logger.critical(msg)

class MaxIterationExceeded(SmoderpError):
    """Number of iteration exceed max iteration criterion.
    """
    def __init__(self, mi, t):
        self.msg = 'Maximum of iterations (max_iter = {}) was exceeded of at time [s]: {}'.format(
            mi, t
        )

    def __str__(self):
        return repr(self.msg)

class NegativeWaterLevel(SmoderpError):

    """Exception raised if the water level goes to negative values.

    """

    def __init__(self):
        self.msg = 'Water level reached negative value'

    def __str__(self):
        return repr(self.msg)
