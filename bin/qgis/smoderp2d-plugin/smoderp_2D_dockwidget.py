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
import sys
import tempfile
import glob

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

# ONLY FOR TESTING PURPOSES (!!!)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from smoderp2d import QGISRunner
from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import ProviderError
from bin.base import arguments, sections

from .connect_grass import find_grass_bin


class InputError(Exception):
    def __init__(self):
        pass


class SmoderpTask(QgsTask):
    def __init__(self, input_params, input_maps, grass_bin_path):
        super().__init__()

        self.input_params = input_params
        self.input_maps = input_maps
        self.grass_bin_path = grass_bin_path
        self.error = None

    def run(self):
        runner = QGISRunner(self.setProgress, self.grass_bin_path)
        runner.set_options(self.input_params)
        runner.import_data(self.input_maps)
        try:
            runner.run()
        except ProviderError as e:
            self.error = e
            return False

        runner.finish()

        # resets
        Globals.reset()
        GridGlobals.reset()

        return True

    def finished(self, result):
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
                'Computation failed: ', str(fail_reason), level=Qgis.Critical
            )


class Smoderp2DDockWidget(QtWidgets.QDockWidget):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
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

        # widgets
        self.elevation_comboBox = QgsMapLayerComboBox()
        self.elevation_toolButton = QtWidgets.QToolButton()
        self.soil_comboBox = QgsMapLayerComboBox()
        self.soil_toolButton = QtWidgets.QToolButton()
        self.soil_type_comboBox = QgsFieldComboBox()
        self.vegetation_comboBox = QgsMapLayerComboBox()
        self.vegetation_toolButton = QtWidgets.QToolButton()
        self.points_comboBox = QgsMapLayerComboBox()
        self.points_toolButton = QtWidgets.QToolButton()
        self.stream_comboBox = QgsMapLayerComboBox()
        self.stream_toolButton = QtWidgets.QToolButton()
        self.rainfall_lineEdit = QtWidgets.QLineEdit()
        self.rainfall_toolButton = QtWidgets.QToolButton()
        self.main_output_lineEdit = QtWidgets.QLineEdit()
        self.main_output_toolButton = QtWidgets.QToolButton()
        self.maxdt_lineEdit = QtWidgets.QSpinBox()
        self.end_time_lineEdit = QtWidgets.QSpinBox()
        self.vegetation_type_comboBox = QgsFieldComboBox()
        self.table_soil_vegetation_comboBox = QgsMapLayerComboBox()
        self.table_soil_vegetation_toolButton = QtWidgets.QToolButton()
        self.table_soil_vegetation_field_comboBox = QgsFieldComboBox()
        self.table_stream_shape_code_comboBox = QgsFieldComboBox()
        self.table_stream_shape_comboBox = QgsMapLayerComboBox()
        self.table_stream_shape_toolButton = QtWidgets.QToolButton()
        self.generate_temporary_checkBox = QtWidgets.QCheckBox()
        self.run_button = QtWidgets.QPushButton(self.dockWidgetContents)

        # set default values
        self.maxdt_lineEdit.setProperty("value", 5)
        self.end_time_lineEdit.setProperty("value", 30)

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
                section_tab_layout.addWidget(argument_label)

                # create empty layout for the specific widget
                argument_widget = QtWidgets.QWidget()
                argument_widget_layout = QtWidgets.QHBoxLayout()
                argument_widget.setLayout(argument_widget_layout)
                section_tab_layout.addWidget(argument_widget)

                self.arguments.update({argument_id: argument_widget_layout})

            section_tab_layout.addStretch()

            section_tab.setLayout(section_tab_layout)

    def set_widgets(self):
        self.arguments['elevation'].addWidget(self.elevation_comboBox)
        self.arguments['elevation'].addWidget(self.elevation_toolButton)
        self.arguments['soil'].addWidget(self.soil_comboBox)
        self.arguments['soil'].addWidget(self.soil_toolButton)
        self.arguments['landuse'].addWidget(self.vegetation_comboBox)
        self.arguments['landuse'].addWidget(self.vegetation_toolButton)
        self.arguments['points'].addWidget(self.points_comboBox)
        self.arguments['points'].addWidget(self.points_toolButton)
        self.arguments['stream'].addWidget(self.stream_comboBox)
        self.arguments['stream'].addWidget(self.stream_toolButton)
        self.arguments['rainfall'].addWidget(self.rainfall_lineEdit)
        self.arguments['rainfall'].addWidget(self.rainfall_toolButton)
        self.arguments['output'].addWidget(self.main_output_lineEdit)
        self.arguments['output'].addWidget(self.main_output_toolButton)
        self.arguments['max_time_step'].addWidget(self.maxdt_lineEdit)
        self.arguments['total_time'].addWidget(self.end_time_lineEdit)
        self.arguments['soil_type_field'].addWidget(self.soil_type_comboBox)
        self.arguments['landuse_type_field'].addWidget(
            self.vegetation_type_comboBox
        )
        self.arguments['soil_landuse_table'].addWidget(
            self.table_soil_vegetation_comboBox
        )
        self.arguments['soil_landuse_table'].addWidget(
            self.table_soil_vegetation_toolButton
        )
        self.arguments['soil_landuse_field'].addWidget(
            self.table_soil_vegetation_field_comboBox
        )
        self.arguments['channel_type_identifier'].addWidget(
            self.table_stream_shape_code_comboBox
        )
        self.arguments['channel_properties'].addWidget(
            self.table_stream_shape_comboBox
        )
        self.arguments['channel_properties'].addWidget(
            self.table_stream_shape_toolButton
        )
        self.arguments['generate_temporary'].addWidget(
            self.generate_temporary_checkBox
        )

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setupButtonSlots(self):
        """Setup buttons slots."""

        # TODO: what if tables are in format that cannot be added to map?
        #  (txt), currently works for dbf

        self.run_button.clicked.connect(self.OnRunButton)

        # 1st tab - Data preparation
        self.elevation_toolButton.clicked.connect(
            lambda: self.openFileDialog('raster', self.elevation_comboBox)
        )
        self.soil_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.soil_comboBox)
        )
        self.vegetation_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.vegetation_comboBox)
        )
        self.points_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.points_comboBox)
        )
        # self.output_toolButton.clicked.connect(
        #        lambda: self.openFileDialog('folder', self.output_lineEdit))
        self.stream_toolButton.clicked.connect(
            lambda: self.openFileDialog('vector', self.stream_comboBox)
        )

        self.soil_comboBox.layerChanged.connect(lambda: self.setFields('soil'))
        self.vegetation_comboBox.layerChanged.connect(
            lambda: self.setFields('vegetation')
        )

        # 2nd tab - Computation
        self.rainfall_toolButton.clicked.connect(
            lambda: self.openFileDialog('file', self.rainfall_lineEdit)
        )

        # 3rd tab - Settings
        self.table_soil_vegetation_toolButton.clicked.connect(
            lambda: self.openFileDialog(
                'table', self.table_soil_vegetation_comboBox
            )
        )
        self.table_stream_shape_toolButton.clicked.connect(
            lambda: self.openFileDialog(
                'table', self.table_stream_shape_comboBox
            )
        )
        self.main_output_toolButton.clicked.connect(
            lambda: self.openFileDialog('folder', self.main_output_lineEdit)
        )

        self.table_soil_vegetation_comboBox.layerChanged.connect(
            lambda: self.setFields('table_soil_veg')
        )
        self.table_stream_shape_comboBox.layerChanged.connect(
            lambda: self.setFields('table_stream_shape')
        )

    def setupCombos(self):
        """Setup combo boxes."""

        # 1st tab - Data preparation
        self.elevation_comboBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.soil_comboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.vegetation_comboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.points_comboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.stream_comboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.setFields('soil')
        self.setFields('vegetation')

        # 3rd tab - Settings
        self.table_soil_vegetation_comboBox.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )
        self.table_stream_shape_comboBox.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )

        self.setFields('table_soil_veg')
        self.setFields('table_stream_shape')

    def set_allow_empty(self):
        self.points_comboBox.setAllowEmptyLayer(True)
        self.stream_comboBox.setAllowEmptyLayer(True)
        self.table_stream_shape_comboBox.setAllowEmptyLayer(True)

    def set_button_texts(self):
        buttons = (
            self.elevation_toolButton, self.soil_toolButton,
            self.vegetation_toolButton, self.points_toolButton,
            self.stream_toolButton, self.main_output_toolButton,
            self.table_soil_vegetation_toolButton,
            self.table_stream_shape_toolButton, self.rainfall_toolButton
        )

        for button in buttons:
            button.setText('...')

    def OnRunButton(self):
        if not self._grass_bin_path:
            # Get GRASS executable
            try:
                self._grass_bin_path = find_grass_bin()
            except ImportError as e:
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
            self.progress_bar = QProgressBar()
            self.progress_bar.setMaximum(100)
            self.progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            messageBar = self.iface.messageBar()
            progress_msg = messageBar.createMessage(
                "Computation progress: "
            )
            progress_msg.layout().addWidget(self.progress_bar)
            messageBar.pushWidget(progress_msg, Qgis.Info)

            smoderp_task.begun.connect(
                lambda: self.progress_bar.setValue(0)
            )
            smoderp_task.progressChanged.connect(
                lambda a: self.progress_bar.setValue(int(a))
            )
            smoderp_task.taskCompleted.connect(self.computationFinished)

            # start the task
            self.task_manager.addTask(smoderp_task)
        else:
            self._sendMessage(
                "Input parameters error:",
                "Some of mandatory fields are not filled correctly.",
                "CRITICAL"
            )

    @staticmethod
    def _layerColorRamp(layer):
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

    def computationFinished(self):
        def import_group_layers(group, outdir, ext='asc', show=False):
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

        # show results
        root = QgsProject.instance().layerTreeRoot()
        group = root.insertGroup(0, self._result_group_name)

        outdir = self.main_output_lineEdit.text().strip()
        import_group_layers(group, outdir, show=True)

        if self._input_params['t']is True:
            temp_group = group.addGroup('temp')
            import_group_layers(temp_group, os.path.join(outdir, 'temp'))
            import_group_layers(temp_group, os.path.join(outdir, 'temp'), 'gml')

        # QGIS bug: group must be collapsed and then expanded
        group.setExpanded(False)
        group.setExpanded(True)

    def _getInputParams(self):
        """Get input parameters from QGIS plugin."""

        self._input_params = {
            'elevation': self.elevation_comboBox.currentText(),
            'soil': self.soil_comboBox.currentText(),
            'soil_type_fieldname': self.soil_type_comboBox.currentText(),
            'vegetation': self.vegetation_comboBox.currentText(),
            'vegetation_type_fieldname':
                self.vegetation_type_comboBox.currentText(),
            'points': self.points_comboBox.currentText(),
            # 'output': self.output_lineEdit.text().strip(),
            'streams': self.stream_comboBox.currentText(),
            'rainfall_file': self.rainfall_lineEdit.text(),
            'end_time': float(self.end_time_lineEdit.text()),
            'maxdt': float(self.maxdt_lineEdit.text()),
            'table_soil_vegetation':
                self.table_soil_vegetation_comboBox.currentText(),
            'table_soil_vegetation_fieldname':
                self.table_soil_vegetation_field_comboBox.currentText(),
            'channel_properties_table':
                self.table_stream_shape_comboBox.currentText(),
            'streams_channel_type_fieldname':
                self.table_stream_shape_code_comboBox.currentText(),
            't': bool(self.generate_temporary_checkBox.checkState()),
            'output': self.main_output_lineEdit.text().strip()
        }

        self._input_maps = {
            'elevation':
                self.elevation_comboBox.currentLayer().dataProvider().dataSourceUri(),
            'soil':
                self.soil_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0],
            'vegetation':
                self.vegetation_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0],
            'points': "",
            'streams': "",
            'table_soil_vegetation':
                self.table_soil_vegetation_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0],
            'channel_properties_table': ""
        }

        # TODO: It would be nicer to use names defined in _input_params before
        # this reparsing
        for key in self._input_maps.keys():
            if self._input_params[key] != '':
                self._input_params[key] = key

        # optional inputs
        if self.points_comboBox.currentLayer() is not None:
            self._input_maps["points"] = \
                self.points_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0]

        if self.stream_comboBox.currentLayer() is not None:
            self._input_maps["streams"] = \
                self.stream_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0]

        if self.table_stream_shape_comboBox.currentLayer() is not None:
            self._input_maps['channel_properties_table'] = \
                self.table_stream_shape_comboBox.currentLayer().dataProvider().dataSourceUri().split('|', 1)[0]
            self._input_maps["streams_channel_type_fieldname"] = self.table_stream_shape_code_comboBox.currentText()

    def _checkInputDataPrep(self):
        """Check mandatory field.

        Check if all mandatory fields are filled correctly for data preparation.
        """

        # Check if none of fields are empty
        if None not in (
                self.elevation_comboBox.currentLayer(),
                self.soil_comboBox.currentLayer(),
                self.soil_type_comboBox.currentText(),
                self.vegetation_comboBox.currentLayer(),
                self.vegetation_type_comboBox.currentText(),
                self.table_soil_vegetation_comboBox.currentLayer(),
                # self.table_soil_vegetation_code_comboBox.currentText(),
                ) and "" not in (
                # self.output_lineEdit.text().strip(),
                self.maxdt_lineEdit.text().strip(),
                self.rainfall_lineEdit.text().strip(),
                self.end_time_lineEdit.text().strip(),
                self.main_output_lineEdit.text().strip()):
            # Check if maxdt and end_time are numbers
            try:
                float(self.maxdt_lineEdit.text())
                float(self.end_time_lineEdit.text())
                return True
            except ValueError:
                return False
        else:
            return False

    def openFileDialog(self, t, widget):
        """Open file dialog, load layer and set path/name to widget."""

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
        """Set fields of soil and vegetation type."""

        if self.soil_comboBox.currentLayer() is not None and t == 'soil':
            self.soil_type_comboBox.setLayer(self.soil_comboBox.currentLayer())
            self.soil_type_comboBox.setField(
                self.soil_comboBox.currentLayer().fields()[0].name()
            )
        elif self.vegetation_comboBox.currentLayer() is not None and t == 'vegetation':
            self.vegetation_type_comboBox.setLayer(
                self.vegetation_comboBox.currentLayer()
            )
            self.vegetation_type_comboBox.setField(
                self.vegetation_comboBox.currentLayer().fields()[0].name()
            )
        elif self.table_soil_vegetation_comboBox.currentLayer() is not None and t == 'table_soil_veg':
            self.table_soil_vegetation_field_comboBox.setLayer(
                self.table_soil_vegetation_comboBox.currentLayer()
            )
            self.table_soil_vegetation_field_comboBox.setField(
                self.table_soil_vegetation_comboBox.currentLayer().fields()[0].name()
            )
        elif t == 'table_stream_shape':
            if self.table_stream_shape_comboBox.currentLayer() is not None:
                self.table_stream_shape_code_comboBox.setLayer(
                    self.table_stream_shape_comboBox.currentLayer()
                )
                self.table_stream_shape_code_comboBox.setField(
                    self.table_stream_shape_comboBox.currentLayer().fields()[0].name())
            else:
                self.table_stream_shape_code_comboBox.setLayer(None)
                self.table_stream_shape_code_comboBox.setField("")

        else:
            pass

    def _sendMessage(self, caption, message, t):
        if t == 'CRITICAL':
            self.iface.messageBar().pushCritical(self.tr(u'{}').format(caption),
                                                 self.tr(u'{}').format(message))
        elif t == 'INFO':
            self.iface.messageBar().pushInfo(self.tr(u'{}').format(caption),
                                             self.tr(u'{}').format(message))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        testAction = menu.addAction("Load test parameters")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == testAction:
            self._loadTestParams()

    def _loadTestParams(self):
        dir_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'tests', 'data'
        )
        try:
            self.elevation_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('dem10m')[0]
            )
            self.soil_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('soils')[0]
            )
            self.points_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('points')[0]
            )
            self.stream_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('stream')[0]
            )
            self.rainfall_lineEdit.setText(
                os.path.join(dir_path, 'rainfall_nucice.txt')
            )
            self.table_soil_vegetation_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('soil_veg_tab_mean')[0]
            )
            self.table_stream_shape_comboBox.setLayer(
                QgsProject.instance().mapLayersByName('stream_shape')[0]
            )
            self.table_stream_shape_code_comboBox.setCurrentText('channel_id')
            with tempfile.NamedTemporaryFile() as temp_dir:
                self.main_output_lineEdit.setText(temp_dir.name)
            self.end_time_lineEdit.setValue(5)
        except IndexError:
            self._sendMessage(
                'Error',
                'Unable to set test parameters. Load demo QGIS project first.',
                'CRITICAL'
            )
