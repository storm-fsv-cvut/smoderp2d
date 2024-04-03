# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Smoderp2DDockWidget
                                 A QGIS plugin
 This plugin computes hydrological erosion model.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-10-10
        git sha              : $Format:%H$
        copyright            : (C) 2018-2020 by CTU
        email                : petr.kavka@fsv.cvut.cz
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import glob
import datetime
import tempfile
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QFileInfo, QSettings, QCoreApplication, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QMenu

from qgis.core import (
    QgsProviderRegistry, QgsMapLayerProxyModel, QgsRasterLayer, QgsTask,
    QgsApplication, Qgis, QgsProject, QgsRasterBandStats,
    QgsSingleBandPseudoColorRenderer, QgsGradientColorRamp, QgsVectorLayer
)
from qgis.utils import iface
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox

from smoderp2d.runners.qgis import QGISRunner
from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers import Logger
from smoderp2d.exceptions import ProviderError, ComputationAborted
from bin.base import arguments, sections

from .connect_grass import find_grass_bin
from .custom_widgets import HistoryWidget


class InputError(Exception):
    """TODO."""

    def __init__(self):
        """TODO."""
        pass


class SmoderpTask(QgsTask):
    """Task holding the SMODERP2D run in a parallel thread."""

    def __init__(self, input_params, input_maps, grass_bin_path, *args,
                 **kwargs):
        """Initialize the task and set its class variables.

        :param input_params: TODO
        :param input_maps: TODO
        :param grass_bin_path: TODO
        """
        super().__init__(*args, **kwargs)

        self.input_params = input_params
        self.input_maps = input_maps
        self.grass_bin_path = grass_bin_path
        self.error = None
        self.finish_msg_level = Qgis.Info
        self.runner = None

    def run(self):
        """Run the task in a parallel thread."""
        try:
            self.runner = QGISRunner(self.setProgress, self.grass_bin_path)
            self.runner.set_options(self.input_params)
            self.runner.import_data(self.input_maps)
            self.runner.run()
        except ProviderError as e:
            self.error = e
            self.finish_msg_level = Qgis.Critical
            return False
        except ComputationAborted:
            self.error = 'Computation was manually aborted.'
            return False

        return True

    def finished(self, result):
        """Handle what should happen once the task is finished.

        :param result: result object containing info on how did the task finish
            (fine, error, aborted...)
        """
        self.runner.finish()

        # resets
        Globals.reset()
        GridGlobals.reset()

        iface.messageBar().findChildren(QtWidgets.QToolButton)[0].setHidden(
            False
        )
        iface.messageBar().clearWidgets()

        if result:
            iface.messageBar().pushMessage(
                'Computation successfully completed', '',
                level=Qgis.Info,
                duration=3
            )
        else:
            if self.error is not None:
                fail_reason = self.error
            else:
                fail_reason = "reason unknown (see SMODERP2D log messages)"

            iface.messageBar().pushMessage(
                'Computation failed: ', str(fail_reason),
                level=self.finish_msg_level
            )


class Smoderp2DDockWidget(QtWidgets.QDockWidget):
    """Class holding the GUI and functionalities of the SMODERP2D plugin."""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor.

        :param parent: TODO
        """
        super(Smoderp2DDockWidget, self).__init__(parent)

        self.iface = iface
        self.task_manager = QgsApplication.taskManager()

        self.settings = QSettings("CTU", "smoderp")
        self.arguments = {}  # filled during self.retranslateUi()
        # (could be set during something more reasonable later)

        # master tabwwidget
        self.dockWidgetContents = QtWidgets.QWidget()
        self.tabWidget = QtWidgets.QTabWidget()
        self.layout = QtWidgets.QVBoxLayout()

        # tabs that need to be kept as self
        self.history_tab = QtWidgets.QListWidget()

        # widgets
        self.elevation = QgsMapLayerComboBox()
        self.elevation_toolButton = QtWidgets.QToolButton()
        self.soil = QgsMapLayerComboBox()
        self.soil_toolButton = QtWidgets.QToolButton()
        self.soil_type = QgsFieldComboBox()
        self.vegetation = QgsMapLayerComboBox()
        self.vegetation_toolButton = QtWidgets.QToolButton()
        self.points = QgsMapLayerComboBox()
        self.points_toolButton = QtWidgets.QToolButton()
        self.points_field = QgsFieldComboBox()
        self.stream = QgsMapLayerComboBox()
        self.stream_toolButton = QtWidgets.QToolButton()
        self.rainfall = QtWidgets.QLineEdit()
        self.rainfall_toolButton = QtWidgets.QToolButton()
        self.main_output = QtWidgets.QLineEdit()
        self.main_output_toolButton = QtWidgets.QToolButton()
        self.maxdt = QtWidgets.QDoubleSpinBox()
        self.end_time = QtWidgets.QDoubleSpinBox()
        self.vegetation_type = QgsFieldComboBox()
        self.table_soil_vegetation = QgsMapLayerComboBox()
        self.table_soil_vegetation_toolButton = QtWidgets.QToolButton()
        self.table_soil_vegetation_field = QgsFieldComboBox()
        self.table_stream_shape_code = QgsFieldComboBox()
        self.table_stream_shape = QgsMapLayerComboBox()
        self.table_stream_shape_toolButton = QtWidgets.QToolButton()
        self.flow_direction = QtWidgets.QComboBox()
        self.generate_temporary = QtWidgets.QCheckBox()
        self.run_button = QtWidgets.QPushButton(self.dockWidgetContents)

        # set default values
        self.maxdt.setValue(5)
        self.maxdt.setMaximum(99999999999999999999999999)
        self.end_time.setValue(30)
        self.end_time.setMaximum(99999999999999999999999999)

        self.retranslateUi()

        self.set_widgets()

        self.set_allow_empty()
        self.set_button_texts()

        self.setupButtonSlots()

        self.setupCombos()

        self.run_button.setText('Run')

        self.layout.addWidget(self.tabWidget)
        self.layout.addWidget(self.run_button)
        self.dockWidgetContents.setLayout(self.layout)
        self.setWidget(self.dockWidgetContents)

        self._result_group_name = "SMODERP2D"
        self._grass_bin_path = None

    def retranslateUi(self):
        """TODO."""
        # TODO: The method should be absolutely called something else
        for section in sections:
            section_tab = QtWidgets.QWidget()
            self.tabWidget.addTab(section_tab, section.label)

            section_tab_layout = QtWidgets.QVBoxLayout()

            for argument_id in section.arguments:
                # add label
                argument_label = QtWidgets.QLabel()
                argument_label.setText(
                    QCoreApplication.translate(
                        self.__class__.__name__, arguments[argument_id].label
                    )
                )

                # create empty layout for the specific widget
                argument_widget = QtWidgets.QWidget()
                argument_widget_layout = QtWidgets.QHBoxLayout()
                argument_widget.setLayout(argument_widget_layout)

                if section.label != 'Advanced':
                    section_tab_layout.addWidget(argument_label)
                else:
                    # so far, all Advanced tab widgets should be horizontal
                    argument_widget_layout.addWidget(argument_label)
                section_tab_layout.addWidget(argument_widget)

                self.arguments.update({argument_id: argument_widget_layout})

            section_tab_layout.addStretch()

            section_tab.setLayout(section_tab_layout)

        # history tab
        section_tab = QtWidgets.QWidget()
        section_tab_layout = QtWidgets.QVBoxLayout()
        section_tab_layout.addWidget(
            QtWidgets.QLabel(
                '25 last calls -- load historical settings by double-click'
            )
        )
        section_tab_layout.addWidget(self.history_tab)
        self._loadHistory()
        section_tab.setLayout(section_tab_layout)

        self.tabWidget.addTab(section_tab, 'History')

    def set_widgets(self):
        """Set the layout of individual widgets."""
        self.arguments['elevation'].addWidget(self.elevation)
        self.arguments['elevation'].addWidget(self.elevation_toolButton)
        self.arguments['soil'].addWidget(self.soil)
        self.arguments['soil'].addWidget(self.soil_toolButton)
        self.arguments['landuse'].addWidget(self.vegetation)
        self.arguments['landuse'].addWidget(self.vegetation_toolButton)
        self.arguments['points'].addWidget(self.points)
        self.arguments['points'].addWidget(self.points_toolButton)
        self.arguments['points_fieldname'].addWidget(self.points_field)
        self.arguments['streams'].addWidget(self.stream)
        self.arguments['streams'].addWidget(self.stream_toolButton)
        self.arguments['rainfall_file'].addWidget(self.rainfall)
        self.arguments['rainfall_file'].addWidget(self.rainfall_toolButton)
        self.arguments['output'].addWidget(self.main_output)
        self.arguments['output'].addWidget(self.main_output_toolButton)
        self.arguments['max_time_step'].addWidget(self.maxdt)
        self.arguments['total_time'].addWidget(self.end_time)
        self.arguments['soil_type_field'].addWidget(self.soil_type)
        self.arguments['landuse_type_field'].addWidget(
            self.vegetation_type
        )
        self.arguments['soil_landuse_table'].addWidget(
            self.table_soil_vegetation
        )
        self.arguments['soil_landuse_table'].addWidget(
            self.table_soil_vegetation_toolButton
        )
        self.arguments['soil_landuse_field'].addWidget(
            self.table_soil_vegetation_field
        )
        self.arguments['streams_channel_type_fieldname'].addWidget(
            self.table_stream_shape_code
        )
        self.arguments['channel_properties_table'].addWidget(
            self.table_stream_shape
        )
        self.arguments['channel_properties_table'].addWidget(
            self.table_stream_shape_toolButton
        )
        self.arguments['flow_direction'].addWidget(
            self.flow_direction
        )
        self.arguments['generate_temporary'].insertWidget(
            0, self.generate_temporary
        )  # checkbox should be before label
        self.arguments['generate_temporary'].addStretch()

    def closeEvent(self, event):
        """TODO.

        :param event: TODO
        """
        self.closingPlugin.emit()
        event.accept()

    def setupButtonSlots(self):
        """Setup buttons slots."""

        # TODO: what if tables are in format that cannot be added to map?
        #  (txt), currently works for dbf

        # run button
        self.run_button.clicked.connect(self.onRunButton)

        # 1ST TAB - SPATIAL DATA
        # clicked signals
        self.elevation_toolButton.clicked.connect(
            lambda: self.openFileDialog('raster', self.elevation)
        )
        self.soil_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.soil)
        )
        self.vegetation_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.vegetation)
        )
        self.points_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.points)
        )
        self.stream_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.stream)
        )
        self.rainfall_toolButton.clicked.connect(
            lambda: self.openFileDialog('file', self.rainfall)
        )

        # layerChanged signals
        self.soil.layerChanged.connect(lambda: self.setFields('soil'))
        self.vegetation.layerChanged.connect(
            lambda: self.setFields('vegetation')
        )
        self.points.layerChanged.connect(
            lambda: self.setFields('points')
        )

        # 2ND TAB - MODEL PARAMETERS
        # clicked signals
        self.table_soil_vegetation_toolButton.clicked.connect(
            lambda: self.openFileDialog(
                'table', self.table_soil_vegetation
            )
        )
        self.table_stream_shape_toolButton.clicked.connect(
            lambda: self.openFileDialog(
                'table', self.table_stream_shape
            )
        )

        # layerChanged signals
        self.table_soil_vegetation.layerChanged.connect(
            lambda: self.setFields('table_soil_veg')
        )
        self.table_stream_shape.layerChanged.connect(
            lambda: self.setFields('channel_properties_table')
        )

        # 3RD TAB - COMPUTATION OPTIONS
        self.main_output_toolButton.clicked.connect(
            lambda: self.openFileDialog('folder', self.main_output)
        )

    def setupCombos(self):
        """Setup combo boxes (set map type filters and add items)."""
        # 1ST TAB - SPATIAL DATA
        self.elevation.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.soil.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.vegetation.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.points.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.stream.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.setFields('soil')
        self.setFields('vegetation')
        self.setFields('points')

        # 2ND TAB - MODEL PARAMETERS
        self.table_soil_vegetation.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )
        self.table_stream_shape.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )

        self.setFields('table_soil_veg')
        self.setFields('channel_properties_table')

        # 4TH TAB - ADVANCED
        self.flow_direction.addItems(('single', 'multiple'))

    def set_allow_empty(self):
        """Set AllowEmptyLayer to True for optional options."""
        self.points.setAllowEmptyLayer(True)
        self.stream.setAllowEmptyLayer(True)
        self.table_stream_shape.setAllowEmptyLayer(True)

    def set_button_texts(self):
        """Set [...] as texts on buttons."""
        buttons = (
            self.elevation_toolButton, self.soil_toolButton,
            self.vegetation_toolButton, self.points_toolButton,
            self.stream_toolButton, self.main_output_toolButton,
            self.table_soil_vegetation_toolButton,
            self.table_stream_shape_toolButton, self.rainfall_toolButton
        )

        for button in buttons:
            button.setText('...')

    def onRunButton(self):
        """Run the processing when the run button was pushed."""
        if not self._grass_bin_path:
            # Get GRASS executable
            try:
                self._grass_bin_path = find_grass_bin()
            except ImportError:
                self._sendMessage(
                    "ERROR:",
                    "GRASS GIS not found.",
                    "CRITICAL"
                )
                return

        if self._checkInputDataPrep():
            # remove previous results
            root = QgsProject.instance().layerTreeRoot()
            result_node = root.findGroup(self._result_group_name)
            if result_node:
                root.removeChildNode(result_node)

            # Get input parameters
            self._getInputParams()

            smoderp_task = SmoderpTask(
                self._input_params, self._input_maps, self._grass_bin_path
            )

            # prepare the progress bar
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            messageBar = self.iface.messageBar()

            messageBar.findChildren(QtWidgets.QToolButton)[0].setHidden(True)

            progress_msg = messageBar.createMessage(
                "Computation progress: "
            )
            progress_msg.layout().addWidget(progress_bar)

            abort_button = QtWidgets.QPushButton(self.dockWidgetContents)
            abort_button.setText('Abort the process')
            abort_button.clicked.connect(self.abort_computation)
            progress_msg.layout().addWidget(abort_button)

            messageBar.pushWidget(progress_msg, Qgis.Info)

            smoderp_task.begun.connect(
                lambda: progress_bar.setValue(0)
            )
            smoderp_task.progressChanged.connect(
                lambda a: progress_bar.setValue(int(a))
            )
            smoderp_task.taskCompleted.connect(self.importResults)

            # start the task
            self.task_manager.addTask(smoderp_task)

            self._addCurrentHistoryItem()
        else:
            self._sendMessage(
                "Input parameters error:",
                "Some of mandatory fields are not filled correctly.",
                "CRITICAL"
            )

    def _loadHistory(self):
        """Load historical runs into History tab.

        If there is no history, set setting[historical_runs] to an empty list.
        """
        # uncomment the following line to reset the history pane
        # self.settings.setValue('historical_runs', None)
        runs = self.settings.value('historical_runs')

        if runs is None:
            self.settings.setValue('historical_runs', [])
        else:
            for run in reversed(runs):
                self._addHistoryItem(run)

    def _addCurrentHistoryItem(self):
        """Add the current run into settings[historical_runs].

        Control that there is no more than 25 historical items holded.

        Then call _addHistoryItem to add the widget to the pane.
        """
        timestamp = str(datetime.datetime.now())
        run = (timestamp, dict(self._input_params), dict(self._input_maps))

        runs = self.settings.value('historical_runs')
        runs.insert(0, run)

        if len(runs) > 25:
            runs.pop(-1)

        self.settings.setValue('historical_runs', runs)

        self._addHistoryItem(run)

    def _addHistoryItem(self, run):
        """Add the historical item to the history pane.

        :param run: The current run info in format (timestamp, params, maps)
        """
        this_run = HistoryWidget(f'{run[1]["output"]} -- {run[0]}')
        try:
            this_run.saveHistory(run[1], run[2])
            self.history_tab.insertItem(0, this_run)
        except (KeyError, IndexError) as e:
            iface.messageBar().pushMessage(
                f'Failed to add historical item {run[0]}: ', str(e),
                level=Qgis.Warning
            )
        self.history_tab.itemDoubleClicked.connect(
            self._loadHistoricalParameters
        )

    @staticmethod
    def _layerColorRamp(layer):
        """Get a renderer with the color ramp set to a layer value extents.

        :param layer: QGIS layer from which to read the values for the ramp
        :return: colr ramp renderer
        """
        # get min/max values
        data_provider = layer.dataProvider()
        stats = data_provider.bandStatistics(
            1, QgsRasterBandStats.All, layer.extent(), 0
        )

        # get colour definitions
        renderer = QgsSingleBandPseudoColorRenderer(data_provider, 1)
        color_ramp = QgsGradientColorRamp(
            QColor(239, 239, 255), QColor(0, 0, 255)
        )
        renderer.setClassificationMin(stats.minimumValue)
        renderer.setClassificationMax(stats.maximumValue)
        renderer.createShader(color_ramp)

        return renderer

    def importResults(self):
        """Import results into QGIS, group them and show them as layers.
        """
        def import_group_layers(group, outdir, ext='asc', show=False):
            """Import individual group layers.

            :param group: QGIS group object
            :param outdir: output directory used during the computation
            :param ext: extension of files to be imported
            :param show: show the layers after import or don't
            """
            for map_path in glob.glob(os.path.join(outdir, f'*.{ext}')):
                if ext == 'asc':
                    # raster
                    layer = QgsRasterLayer(
                        map_path,
                        os.path.basename(os.path.splitext(map_path)[0])
                    )

                    # set symbology
                    layer.setRenderer(self._layerColorRamp(layer))
                else:
                    # vector
                    layer = QgsVectorLayer(
                        map_path,
                        os.path.basename(os.path.splitext(map_path)[0])
                    )

                # add layer into group
                QgsProject.instance().addMapLayer(layer, False)
                node = group.addLayer(layer)
                node.setExpanded(False)
                node.setItemVisibilityChecked(show is True)
                show = False

        # show main results
        root = QgsProject.instance().layerTreeRoot()
        group = root.insertGroup(0, self._result_group_name)

        outdir = self.main_output.text().strip()
        import_group_layers(group, outdir, show=True)

        # import control results
        ctrl_group = group.addGroup('control')
        ctrl_group.setExpanded(False)
        ctrl_group.setItemVisibilityChecked(False)
        import_group_layers(ctrl_group, os.path.join(outdir, 'control'))

        # import control points
        ctrl_group = group.addGroup('control_point')
        ctrl_group.setExpanded(False)
        ctrl_group.setItemVisibilityChecked(False)
        import_group_layers(
            ctrl_group, os.path.join(outdir, 'control_point'), 'csv'
        )

        if self._input_params['generate_temporary'] is True:
            # import temp results
            temp_group = group.addGroup('temp')
            temp_group.setExpanded(False)
            temp_group.setItemVisibilityChecked(False)
            import_group_layers(temp_group, os.path.join(outdir, 'temp'))
            import_group_layers(temp_group, os.path.join(outdir, 'temp'), 'gml')

        # QGIS bug: group must be collapsed and then expanded
        group.setExpanded(False)
        group.setExpanded(True)

    def _getInputParams(self):
        """Get input parameters from QGIS plugin."""
        def get_map_path(data_provider):
            """Get path to a map.

            :param data_provider: qgis_layer.dataProvider()
            :return: path to the source map as a string
            """
            name = data_provider.name()
            uri = data_provider.dataSourceUri()
            if name in ('ogr', 'gdal'):
                ret = uri.split('|', 1)[0]
            elif name == 'delimitedtext':
                ret = uri.split('?')[0].split('file://')[1]
            else:
                raise ProviderError(
                    f'Unknown type of layer {data_provider.dataSourceUri()}'
                )

            return ret

        self._input_params = {
            'elevation': self.elevation.currentText(),
            'soil': self.soil.currentText(),
            'soil_type_fieldname': self.soil_type.currentText(),
            'vegetation': self.vegetation.currentText(),
            'vegetation_type_fieldname': self.vegetation_type.currentText(),
            'points': self.points.currentText(),
            'points_fieldname': self.points_field.currentText(),
            # 'output': self.output_lineEdit.text().strip(),
            'streams': self.stream.currentText(),
            'rainfall_file': self.rainfall.text(),
            'end_time': self.end_time.value(),
            'maxdt': self.maxdt.value(),
            'table_soil_vegetation': self.table_soil_vegetation.currentText(),
            'table_soil_vegetation_fieldname':
                self.table_soil_vegetation_field.currentText(),
            'channel_properties_table': self.table_stream_shape.currentText(),
            'streams_channel_type_fieldname':
                self.table_stream_shape_code.currentText(),
            'flow_direction': self.flow_direction.currentText(),
            'generate_temporary': bool(self.generate_temporary.checkState()),
            'output': self.main_output.text().strip()
        }

        self._input_maps = {
            'elevation':
                get_map_path(self.elevation.currentLayer().dataProvider()),
            'soil':
                get_map_path(self.soil.currentLayer().dataProvider()),
            'vegetation':
                get_map_path(self.vegetation.currentLayer().dataProvider()),
            'points': "",
            'streams': "",
            'table_soil_vegetation': get_map_path(
                self.table_soil_vegetation.currentLayer().dataProvider()
            ),
            'channel_properties_table': ""
        }

        # TODO: It would be nicer to use names defined in _input_params before
        # this reparsing
        for key in self._input_maps.keys():
            if self._input_params[key] != '':
                self._input_params[key] = key

        # optional inputs
        if self.points.currentLayer() is not None:
            self._input_maps["points"] = get_map_path(
                self.points.currentLayer().dataProvider()
            )

        if self.stream.currentLayer() is not None:
            self._input_maps["streams"] = get_map_path(
                self.stream.currentLayer().dataProvider()
            )

        if self.table_stream_shape.currentLayer() is not None:
            self._input_maps['channel_properties_table'] = get_map_path(
                self.table_stream_shape.currentLayer().dataProvider()
            )
            self._input_maps["streams_channel_type_fieldname"] = self.table_stream_shape_code.currentText()

    def _checkInputDataPrep(self):
        """Check mandatory fields.

        Check if all mandatory fields are filled correctly for data preparation.

        :return: boolean saying if mandatory fields are correctly set or not
        """
        # Check if none of fields are empty
        if None not in (
                self.elevation.currentLayer(),
                self.soil.currentLayer(),
                self.soil_type.currentText(),
                self.vegetation.currentLayer(),
                self.vegetation_type.currentText(),
                self.table_soil_vegetation.currentLayer(),
                ) and "" not in (
                self.maxdt.text().strip(),
                self.rainfall.text().strip(),
                self.end_time.text().strip(),
                self.main_output.text().strip()):
            return True
        else:
            return False

    def openFileDialog(self, t, widget):
        """Open file dialog, load layer and set path/name to widget.

        :param t: layer type (raster or vector)
        :param widget: widget that will be set to the layer corresponding to
            the chosen file
        """
        # TODO: what format can tables have?
        # TODO: set layers srs on loading

        # remember last folder where user was in
        sender = u'{}-last_used_file_path'.format(self.sender().objectName())
        last_used_file_path = self.settings.value(sender, '')

        if t == 'vector':
            vector_filters = QgsProviderRegistry.instance().fileVectorFilters()
            file_name = QFileDialog.getOpenFileName(
                self, self.tr(u'Open file'),
                self.tr(u'{}').format(last_used_file_path),
                vector_filters
            )[0]
            if file_name:
                name, file_extension = os.path.splitext(file_name)
                if file_extension not in vector_filters:
                    self._sendMessage(
                        u'Error', u'{} is not a valid vector layer.'.format(
                            file_name
                        ),
                        'CRITICAL'
                    )
                    return

                self.iface.addVectorLayer(
                    file_name, QFileInfo(file_name).baseName(), "ogr"
                )
                widget.setLayer(self.iface.activeLayer())
                self.settings.setValue(sender, os.path.dirname(file_name))
        elif t == 'raster':
            raster_filters = QgsProviderRegistry.instance().fileRasterFilters()
            file_name = QFileDialog.getOpenFileName(
                self, self.tr(u'Open file'),
                self.tr(u'{}').format(last_used_file_path),
                raster_filters
            )[0]
            if file_name:
                name, file_extension = os.path.splitext(file_name)

                if file_extension not in raster_filters:
                    self._sendMessage(
                        u'Error', u'{} is not a valid raster layer.'.format(
                            file_name
                        ),
                        'CRITICAL'
                    )
                    return

                self.iface.addRasterLayer(
                    file_name, QFileInfo(file_name).baseName()
                )
                widget.setLayer(self.iface.activeLayer())
                self.settings.setValue(sender, os.path.dirname(file_name))
        elif t == 'folder':
            folder_name = QFileDialog.getExistingDirectory(
                self, self.tr(u'Select directory'),
                self.tr(u'{}').format(last_used_file_path)
            )

            if os.access(folder_name, os.W_OK):
                widget.setText(folder_name)
                self.settings.setValue(sender, os.path.dirname(folder_name))
            elif folder_name == "":
                pass
            else:
                self._sendMessage(
                    u'Error',
                    u'{} is not writable.'.format(folder_name),
                    'CRITICAL'
                )
        elif t == 'table':
            # write path to file to lineEdit
            file_name = QFileDialog.getOpenFileName(
                self, self.tr(u'Open file'),
                self.tr(u'{}').format(last_used_file_path)
            )[0]

            if file_name:
                self.iface.addVectorLayer(
                    file_name, QFileInfo(file_name).baseName(), "ogr"
                )
                widget.setLayer(self.iface.activeLayer())
                self.settings.setValue(sender, os.path.dirname(file_name))
        elif t == 'file':
            # write path to file to lineEdit
            file_name = QFileDialog.getOpenFileName(
                self,
                self.tr(u'Open file'),
                self.tr(u'{}').format(last_used_file_path)
            )[0]

            if file_name:
                widget.setText(file_name)
                self.settings.setValue(sender, os.path.dirname(file_name))
        else:
            pass

    def setFields(self, t):
        """Set fields of soil and vegetation type.

        :param t: type of field to be set
        """
        if t == 'soil':
            self.setField(
                self.soil.currentLayer(), self.soil_type
            )
        elif t == 'vegetation':
            self.setField(
                self.vegetation.currentLayer(),
                self.vegetation_type
            )
        elif t == 'table_soil_veg':
            self.setField(
                self.table_soil_vegetation.currentLayer(),
                self.table_soil_vegetation_field
            )
        elif t == 'vegetation':
            self.setField(
                self.vegetation.currentLayer(),
                self.vegetation_type
            )
        elif t == 'channel_properties_table':
            self.setField(
                self.table_stream_shape.currentLayer(),
                self.table_stream_shape_code
            )
        elif t == 'points':
            self.setField(
                self.points.currentLayer(),
                self.points_field
            )

    @staticmethod
    def setField(current_layer, widget):
        """Set a widget to the first field from the current layer.

        :param current_layer: layer from which the fields are read
        :param widget: widget where the field should be set as a value
        """
        if current_layer is not None:
            widget.setLayer(current_layer)
            widget.setField(current_layer.fields()[0].name())
        else:
            widget.setLayer(None)
            widget.setField(None)

    def _sendMessage(self, caption, message, t):
        """Tell the user what's going on in the process.

        :param caption: title of the message
        :param message: message to be shown
        :param t: type of message (CRITICAL, INFO)
        """
        if t == 'CRITICAL':
            self.iface.messageBar().pushCritical(self.tr(u'{}').format(caption),
                                                 self.tr(u'{}').format(message))
        elif t == 'INFO':
            self.iface.messageBar().pushInfo(self.tr(u'{}').format(caption),
                                             self.tr(u'{}').format(message))

    def contextMenuEvent(self, event):
        """Roll out the right-click menu.

        :param event: TODO
        """
        menu = QMenu(self)
        testAction = menu.addAction("Load test parameters")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == testAction:
            self._loadTestParams()

    def _loadTestParams(self):
        """Load test parameters into the GUI."""
        try:
            project = QgsProject.instance()
            project_path = project.readPath("./")
            project_dirname = Path(project_path).name
            with tempfile.NamedTemporaryFile() as temp_dir:
                param_dict = {
                    'elevation': project.mapLayersByName('dem')[0],
                    'soil': project.mapLayersByName('soils')[0],
                    'soil_type_fieldname': 'Soil',
                    'vegetation': project.mapLayersByName('landuse')[0],
                    'vegetation_type_fieldname': 'LandUse',
                    'points': project.mapLayersByName('points')[0],
                    'points_fieldname': 'point_id',
                    'streams': project.mapLayersByName('streams')[0],
                    'rainfall_file': os.path.join(Path(project_path).parent, f'rainfall_{project_dirname}.txt'),
                    'table_soil_vegetation': project.mapLayersByName('soil_veg_tab')[0],
                    'table_soil_vegetation_fieldname': 'soilveg',
                    'channel_properties_table': project.mapLayersByName('streams_shape')[0],
                    'streams_channel_type_fieldname': 'channel_id',
                    'output': temp_dir.name,
                    'end_time': 5,
                    'flow_direction': 'single',
                    'generate_temporary': True
                }
            self._loadParams(param_dict)
        except IndexError as e:
            self._sendMessage(
                'Error',
                f'Unable to set test parameters: {e}. Load demo QGIS project first.',
                'CRITICAL'
            )

    def _loadHistoricalParameters(self, historical_widget):
        """Load historical parameters into the GUI.

        :param historical_widget:
        """
        self._loadParams(historical_widget.params_dict)

    def _loadParams(self, param_dict):
        """Load parameters from a dictionary into the GUI.

        :param param_dict: dict in form {parameter_name: parameter_value}
        """
        self.elevation.setLayer(param_dict['elevation'])
        self.soil.setLayer(param_dict['soil'])
        self.soil_type.setCurrentText(param_dict['soil_type_fieldname'])
        self.vegetation.setLayer(param_dict['vegetation'])
        self.vegetation_type.setCurrentText(param_dict['vegetation_type_fieldname'])
        self.points.setLayer(param_dict['points'])
        self.points_field.setCurrentText(
            param_dict['points_fieldname']
        )
        self.stream.setLayer(param_dict['streams'])
        self.rainfall.setText(param_dict['rainfall_file'])
        self.table_soil_vegetation.setLayer(
            param_dict['table_soil_vegetation']
        )
        self.table_soil_vegetation_field.setCurrentText(
            param_dict['table_soil_vegetation_fieldname']
        )
        self.table_stream_shape.setLayer(
            param_dict['channel_properties_table']
        )
        self.table_stream_shape_code.setCurrentText(
            param_dict['streams_channel_type_fieldname']
        )
        self.main_output.setText(param_dict['output'])
        self.end_time.setValue(param_dict['end_time'])
        self.flow_direction.setCurrentText(param_dict['flow_direction'])
        self.generate_temporary.setChecked(param_dict['generate_temporary'])

    def abort_computation(self):
        """Abort the computation.

        Sets Logger.aborted to True
        """
        tasks = self.task_manager.tasks()
        if len(tasks) > 0:
            iface.messageBar().pushMessage(
                'Computation aborted. Stopping the process...',
                level=Qgis.Info
            )
            Logger.aborted = True
