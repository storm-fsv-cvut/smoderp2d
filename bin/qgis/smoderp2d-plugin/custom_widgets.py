import os

from PyQt5.QtWidgets import QListWidgetItem
from qgis.core import QgsProject


class HistoryWidget(QListWidgetItem):
    """QListWidget that is able to hold info on historical parameterization."""

    def __init__(self, *args, **kwargs):
        """Initialize an instance.

        Create an empty self.params_dict dictionary and then do
        the QListWidgetItem things.
        """
        self.params_dict = {}
        super().__init__(*args, **kwargs)

    def saveHistory(self, params):
        """Save historical parameterization into class variables.

        :param params: parameters from the current run
        """
        instance = QgsProject.instance()

        # collect map layers
        map_layers = {}
        for lyr in instance.mapLayers().values():
            map_layers[lyr.source()] = lyr

        # add tooltip
        self.setToolTip(str(params))

        # update spatial data related items
        for key in ("elevation", "soil", "vegetation", "points", "streams",
                    "table_soil_vegetation", "channel_properties_table"):
            if params[key]:
                params[key] = map_layers.get(params[key], None)
        print(params)
        self.params_dict.update(params)
