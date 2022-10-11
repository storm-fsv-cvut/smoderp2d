# TODO: cyclic import...
from smoderp2d.providers import Logger

class SmoderpError(Exception):
    def __init__(self, msg):
        Logger.fatal(msg)

class ProviderError(Exception):
    def __init__(self, msg):
        Logger.fatal(msg)

class MaxIterationExceeded(SmoderpError):
    """Number of iteration exceed max iteration criterion.
    """
    def __init__(self, mi, t):
        self.msg = 'Maximum of iterations (max_iter = {}) was exceeded of at time [s]: {}'.format(
            mi, t
        )
        super().__init__(self.msg)

    def __str__(self):
        return self.msg

class GlobalsNotSet(SmoderpError):
    """Exception raised if globals called variable is None.

    """
    def __init__(self):
        Logger.fatal(
            'Global variable is still None'
        )

class NegativeWaterLevel(SmoderpError):
    """Exception raised if the water level goes to negative values.

    """
    def __init__(self):
        Logger.fatal(
            'Water level reached negative value'
        )

class ConfigError(Exception):
    def __str__(self):
        return self.msg

class SmallParameterValue(ConfigError):
    """ Exception raised if a parameter reaches a wrong numeric value
    """
    def __init__(self,param,value,limit):
        self.msg = "Parameter '{}' has low value ({} < {}).".format(
                param,value,limit)
        super().__init__(self.msg)

class LargeParameterValue(ConfigError):
    """ Exception raised if a parameter reaches a wrong numeric value
    """
    def __init__(self,param,value,limit):
        self.msg = "Parameter '{}' has a wrong value ({} > {}).".format(
                param,value,limit)
        super().__init__(self.msg)

class WrongParameterValue(ConfigError):
    """ Exception raised if a parameter reaches a wrong numeric value
    """
    def __init__(self,param,value):
        self.msg = "Parameter '{}' has a wrong value ({}).".format(param,value)
        super().__init__(self.msg)
