from PyQt5.QtWidgets import QListWidgetItem


class HistoryWidget(QListWidgetItem):
    """QListWidget that is able to hold info on historical parameterization."""

    def __init__(self, *args, **kwargs):
        self.params_dict = {}
        super().__init__(*args, **kwargs)

    def saveHistory(self, params, maps):
        """Save historical parameterization into class variables.

        :param params: parameters from the current run
        :param maps: maps from the current run
        """
        self.params_dict.update(params)
        self.params_dict.update(maps)
