from smoderp2d.providers.base import Logger


class DataPreparationError(Exception):
    pass


class DataPreparationInvalidInput(DataPreparationError):
    def __init__(self, msg):
        Logger.fatal(
            "Invalid input for data preparation: {}".format(msg)
        )


class LicenceNotAvailable(DataPreparationError):
    def __init__(self, msg):
        Logger.fatal(
            "Essential software licence missing: {}".format(msg)
        )


class DataPreparationNoIntersection(DataPreparationError):
    def __init__(self):
        Logger.fatal(
            "The input layers are not correct! "
            "The geometrical intersection of input datasets is empty."
        )
