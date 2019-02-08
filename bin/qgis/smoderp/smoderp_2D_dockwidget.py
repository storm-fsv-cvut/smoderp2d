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
        copyright            : (C) 2018 by CTU
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, QFileInfo, QSettings

from PyQt5.QtWidgets import QFileDialog
from qgis.core import QgsProviderRegistry
from qgis.utils import iface

from smoderp2d.exceptions import ProviderError
from smoderp2d import QGISRunner
from .connect_grass import findGrass as fg

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'smoderp_2D_dockwidget_base.ui'))


class Smoderp2DDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(Smoderp2DDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface

        self.settings = QSettings("CTU", "smoderp")

        self.setup_buttons()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setup_buttons(self):
        """Setup buttons slots."""

        self.run_dataprep.clicked.connect(self.on_run_button)
        self.elevation_toolButton.clicked.connect(lambda: self._open_file_dialog('raster', 'elevation', self.elevation_lineEdit))
        self.soil_toolButton.clicked.connect(lambda: self._open_file_dialog('vector', 'soil', self.soil_lineEdit))

    def on_run_button(self):

        # Get grass
        grass7bin = fg()

        # Get input parameters
        self._get_input_params()

        try:
            runner = QGISRunner()

        except ProviderError as e:
            raise ProviderError(e)

    def _get_input_params(self):
        """Get input parameters from QGIS plugin."""

        self._input_params = {
            'elevation': self.elevation_lineEdit.text(),
            'soil': self.soil_lineEdit.text(),
            'soil_type': self.soil_type_comboBox.currentText(),
            'vegetation': self.vegetation_lineEdit.text(),
            'vegetation_type': self.vegetation_type_comboBox.currentText(),
            'points': self.points_lineEdit.text(),
            'output': self.output_lineEdit.text(),
            'stream': self.stream_lineEdit.text(),
            'pickle': self.pickle_lineEdit.text(),
            'rainfall_file': self.rainfall_file_lineEdit.text(),
            'end_time': float(self.end_time_lineEdit.text()) * 60.0, # prevod na s
            'maxdt': float(self.maxdt_lineEdit.text()),
            'table_soil_vegetation': self.table_soil_vegetation_lineEdit.text(),
            'table_soil_vegetation_code': self.table_soil_vegetation_code_comboBox.currentText(),
            'table_stream_shape': self.table_stream_shape_lineEdit.text(),
            'table_stream_shape_code': self.table_stream_shape_code_comboBox.currentText(),
            'main_output': self.main_output_lineEdit.text()
        }

    def _open_file_dialog(self, t, key, line_edit):
        """Open file dialog, return file."""

        # remember last folder where user was in
        sender = u'{}-last_used_file_path'.format(self.sender().objectName())
        last_used_file_path = self.settings.value(sender, '')

        if t == 'vector':
            file_name = QFileDialog.getOpenFileName(self, self.tr(u'Open file'),
                                                    self.tr(u'{}').format(last_used_file_path),
                                                    QgsProviderRegistry.instance().fileVectorFilters())[0]
            if file_name:
                name, file_extension = os.path.splitext(file_name)

                if file_extension not in QgsProviderRegistry.instance().fileVectorFilters():
                    self.send_message(u'Error', u'{} is not a valid vector layer.'.format(file_name), 'CRITICAL')
                    return

                self.iface.addVectorLayer(file_name, QFileInfo(file_name).baseName(), "ogr")

                line_edit.setText(file_name)

                # set up combo boxes
                if key in ('soil', 'vegetation'):
                    self._setup_combo(key)

        elif t == 'raster':
            file_name = QFileDialog.getOpenFileName(self, self.tr(u'Open file'),
                                                    self.tr(u'{}').format(last_used_file_path),
                                                    QgsProviderRegistry.instance().fileRasterFilters())[0]
            if file_name:
                name, file_extension = os.path.splitext(file_name)

                if file_extension not in QgsProviderRegistry.instance().fileRasterFilters():
                    self.send_message(u'Error', u'{} is not a valid raster layer.'.format(file_name), 'CRITICAL')
                    return

                self.iface.addRasterLayer(file_name, QFileInfo(file_name).baseName())

                line_edit.setText(file_name)
                self.settings.setValue(sender, os.path.dirname(file_name))

        # TODO: do the same for tables

    def _setup_combo(self, key):
        pass

    def send_message(self, caption, message, t):
        if t == 'CRITICAL':
            self.iface.messageBar().pushCritical(self.tr(u'{}').format(caption),
                                                 self.tr(u'{}').format(message))
        elif t == 'INFO':
            self.iface.messageBar().pushInfo(self.tr(u'{}').format(caption),
                                             self.tr(u'{}').format(message))
