# TODO: cyclic import...
from smoderp2d.providers import Logger


class SmoderpError(Exception):
    """TODO."""

    def __init__(self, msg=None):
        """TODO.

        :param msg: TODO
        """
        Logger.fatal(msg)


class ProviderError(Exception):
    """TODO."""

    def __init__(self, msg=None):
        """TODO.

        :param msg: TODO
        """
        Logger.fatal(msg)


class MaxIterationExceeded(SmoderpError):
    """Number of iteration exceed max iteration criterion."""

    def __init__(self, mi, t):
        """TODO.

        :param mi: TODO
        :param t: TODO
        """
        self.msg = 'Maximum of iterations (max_iter = {}) was exceeded of ' \
                   'at time [s]: {}'.format(mi, t)
        super().__init__(self.msg)

    def __str__(self):
        """TODO."""
        return self.msg


class GlobalsNotSet(SmoderpError):
    """Exception raised if globals called variable is None."""

    def __init__(self):
        """TODO."""
        Logger.fatal(
            'Global variable is still None'
        )


class NegativeWaterLevel(SmoderpError):
    """Exception raised if the water level goes to negative values."""

    def __init__(self):
        """TODO."""
        Logger.fatal(
            'Water level reached negative value'
        )


class ConfigError(Exception):
    """TODO."""

    pass


class SmallParameterValueError(ConfigError):
    """ Exception raised if a parameter reaches a wrong (too small) numeric value
    """
    def __init__(self, param, value, limit):
        self.msg = "Parameter '{}' has low value ({} < {}).".format(
                param, value, limit
        )
        Logger.fatal(self.msg)


class LargeParameterValueError(ConfigError):
    """ Exception raised if a parameter reaches a wrong (too large) numeric value
    """
    def __init__(self, param, value, limit):
        self.msg = "Parameter '{}' has a wrong value ({} > {}).".format(
                param, value, limit
        )
        Logger.fatal(self.msg)


class WrongParameterValue(ConfigError):
    """ Exception raised if a parameter reaches a wrong numeric value
    """
    def __init__(self, param, value):
        self.msg = "Parameter '{}' has a wrong value ({}).".format(
            param, value
        )
        Logger.fatal(self.msg)

class ComputationAborted(SmoderpError):
    """Raised when the computation was aborted through an expected signal."""

    def __init__(self, msg=None):
        """Let the user through logger know what has happened.

        :param msg: message to be reported at info level instead of the
            default one
        """
        if msg is not None:
            self.msg = msg
        else:
            self.msg = 'The computation was manually aborted.'

        Logger.info(self.msg)

    def __str__(self):
        """Represent the object as a string."""
        return self.msg

