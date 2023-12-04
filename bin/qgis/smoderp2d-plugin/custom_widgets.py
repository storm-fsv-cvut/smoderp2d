import os

from PyQt5.QtWidgets import QListWidgetItem

from qgis.core import QgsProject


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
        instance = QgsProject.instance()
        map_names = {
            i: instance.mapLayersByName(os.path.split(os.path.splitext(j)[0])[1]) for i, j in maps.items()
        }
        self.params_dict.update({
            'elevation': map_names['elevation'][0],
            'soil': map_names['soil'][0],
            'points': map_names['points'][0],
            'points_fieldname': params['points_fieldname'],
            'streams': map_names['streams'][0],
            'rainfall_file': params['rainfall_file'],
            'table_soil_vegetation': map_names['table_soil_vegetation'][0],
            'channel_properties_table': map_names['channel_properties_table'][0],
            'streams_channel_type_fieldname': params[
                'streams_channel_type_fieldname'
            ],
            'output': params['output'],
            'end_time': params['end_time'],
            'flow_direction': params['flow_direction'],
            'generate_temporary': params['generate_temporary']
        })

        self.setToolTip(str(self.params_dict))
