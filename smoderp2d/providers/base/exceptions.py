from smoderp2d.providers.base import Logger

class DataPreparationError(Exception):
    pass

class DataPreparationInvalidInput(DataPreparationError):
    def __init__(self, msg):
        Logger.fatal(
            "Invalid input for data preparation: {}".format(msg)
        )
