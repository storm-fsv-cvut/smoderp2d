# -*- coding: utf-8 -*-

import arcpy
import sys
import os

py3 = sys.version_info[0] == 3
if py3:
    from importlib import reload

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from smoderp2d import ArcGisRunner
from smoderp2d.providers.base import CompType
from smoderp2d.exceptions import ProviderError

# input parameters constants
PARAMETER_DEM = 0
PARAMETER_SOIL = 1
PARAMETER_SOIL_TYPE = 2
PARAMETER_VEGETATION = 3
PARAMETER_VEGETATION_TYPE = 4
PARAMETER_PATH_TO_RAINFALL_FILE = 5
PARAMETER_MAX_DELTA_T = 6
PARAMETER_END_TIME = 7
#PARAMETER_SURFACE_RETENTION = 6  # nula jen docasne, typ vypoctu se resi jinak
PARAMETER_POINTS = 8
PARAMETER_SOILVEGTABLE = 9
PARAMETER_SOILVEGTABLE_CODE = 10
PARAMETER_STREAM = 11
PARAMETER_STREAMTABLE = 12
PARAMETER_STREAMTABLE_CODE = 13
PARAMETER_DATAPREP_ONLY = 14
PARAMETER_PATH_TO_OUTPUT_DIRECTORY = 15

class Toolbox(object):
    def __init__(self):
        """Set of tools for preparation and executing the SMODERP2D soil erosion model"""
        self.label = "SMODERP2D tools"
        self.alias = ""
        self.description = "Set of tools for executing the SMODERP2D soil erosion model\n" \
            "Department of Irrigation, Drainage and Landscape Water Management\nFaculty of Civil " \
            "Engineering, Czech Technical University. 2022"

        # List of tool classes associated with this toolbox
        self.tools = [SMODERP2D]

class SMODERP2D(object):
    def __init__(self):
        """The tool to execute the SMODERP model"""
        self.label = "SMODERP2D"
        self.description = ""
        self.canRunInBackground = False
        self.category = ""

    def getParameterInfo(self):
        """Define parameter definitions"""
        inputSurfaceRaster = arcpy.Parameter(
           displayName="Input surface raster",
           name="inputSurfaceRaster",
           datatype="GPRasterLayer",
           parameterType="Required",
           direction="Input"
        )
        inputSoilPolygons = arcpy.Parameter(
           displayName="Soil polygons feature layer",
           name="inputSoilPolygons",
           datatype="GPFeatureLayer",
           parameterType="Required",
           direction="Input"
        )
        soilTypefieldName = arcpy.Parameter(
           displayName="Field with the soil type identifier",
           name="soilTypefieldName",
           datatype="Field",
           parameterType="Required",
           direction="Input",
        )
        soilTypefieldName.parameterDependencies = [inputSoilPolygons.name]

        inputLUPolygons = arcpy.Parameter(
           displayName="Landuse polygons feature layer",
           name="inputLUPolygons",
           datatype="GPFeatureLayer",
           parameterType="Required",
           direction="Input"
        )
        LUtypeFieldName = arcpy.Parameter(
           displayName="Field with the landuse type identifier",
           name="LUtypeFieldName",
           datatype="Field",
           parameterType="Optional",
           direction="Input",
        )
        LUtypeFieldName.parameterDependencies = [inputLUPolygons.name]

        inputRainfall = arcpy.Parameter(
           displayName="Definition of the rainfall event",
           name="inputRainfall",
           datatype="DEFile",
           parameterType="Required",
           direction="Input"
        )
        inputRainfall.filter.list = ["txt"]

        maxTimeStep = arcpy.Parameter(
           displayName="Maximum time step [s]",
           name="maxTimeStep",
           datatype="GPDouble",
           parameterType="Optional",
           direction="Input",
           category="Settings"
        )
        maxTimeStep.value = 30

        totalRunTime = arcpy.Parameter(
           displayName="Total running time [min]",
           name="totalRunTime",
           datatype="GPDouble",
           parameterType="Optional",
           direction="Input",
           category="Settings"
        )
        totalRunTime.value = 40

        inputPoints = arcpy.Parameter(
           displayName="Input points feature layer",
           name="inputPoints",
           datatype="GPFeatureLayer",
           parameterType="Optional",
           direction="Input"
        )

        soilvegPropertiesTable = arcpy.Parameter(
           displayName="Soils and Landuse parameters table",
           name="soilvegPropertiesTable",
           datatype="GPTableView",
           parameterType="Required",
           direction="Input"
        )
        soilvegIDfieldName = arcpy.Parameter(
           displayName="Field with the landuse type identifier",
           name="soilvegIDfieldName",
           datatype="Field",
           parameterType="Required",
           direction="Input",
        )
        soilvegIDfieldName.parameterDependencies = [soilvegPropertiesTable.name]

        streamNetwork = arcpy.Parameter(
           displayName="Stream network feature layer",
           name="streamNetwork",
           datatype="GPFeatureLayer",
           parameterType="Optional",
           direction="Input"
        )
        streamNetwork.filter.list = ["Polyline"]

        channelTypesTable = arcpy.Parameter(
           displayName="Channel properties table",
           name="channelTypesTable",
           datatype="GPTableView",
           parameterType="Optional",
           direction="Input"
        )
        channelIDfieldName = arcpy.Parameter(
           displayName="Field with the channel type identifier",
           name="channelIDfieldName",
           datatype="Field",
           parameterType="Optional",
           direction="Input",
        )
        channelIDfieldName.parameterDependencies = [channelTypesTable.name]

        dataprepOnly = arcpy.Parameter(
           displayName="Do the data preparation only",
           name="dataprepOnly",
           datatype="GPBoolean",
           parameterType="Optional",
           direction="Input",
           category="Settings"
        )
        dataprepOnly.value = False

        outDir = arcpy.Parameter(
           displayName="Output folder",
           name="outDir",
           datatype="DEWorkspace",
           parameterType="Required",
           direction="Input"
        )
        outDir.filter.list = ["File System"]

        return [
            inputSurfaceRaster, inputSoilPolygons, soilTypefieldName,
            inputLUPolygons, LUtypeFieldName, inputRainfall,
            maxTimeStep, totalRunTime, inputPoints,
            soilvegPropertiesTable, soilvegIDfieldName, streamNetwork,
            channelTypesTable, channelIDfieldName, dataprepOnly, outDir,
        ]

    def updateParameters(self, parameters):
        """Values and properties of parameters before internal validation is performed.
        This method is called whenever a parameter has been changed."""
        return

    def updateMessages(self, parameters):
        """Messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            runner = ArcGisRunner()

            runner.set_options(
                self._get_input_params(parameters)
            )
            if parameters[PARAMETER_DATAPREP_ONLY].value:
                runner.set_comptype(comp_type=CompType.dpre)

            runner.run()
        except ProviderError as e:
            arcpy.AddError(e)

        return

    @staticmethod
    def _get_input_params(parameters):
        """Get input parameters from ArcGIS toolbox.
        """
        return {
            'elevation': parameters[PARAMETER_DEM].valueAsText,
            'soil': parameters[PARAMETER_SOIL].valueAsText,
            'soil_type': parameters[PARAMETER_SOIL_TYPE].valueAsText,
            'vegetation': parameters[PARAMETER_VEGETATION].valueAsText,
            'vegetation_type': parameters[PARAMETER_VEGETATION_TYPE].valueAsText,
            'rainfall_file': parameters[PARAMETER_PATH_TO_RAINFALL_FILE].valueAsText,
            'maxdt': float(parameters[PARAMETER_MAX_DELTA_T].valueAsText),
            'end_time': float(parameters[PARAMETER_END_TIME].valueAsText),
            'points': parameters[PARAMETER_POINTS].valueAsText,
            'table_soil_vegetation': parameters[PARAMETER_SOILVEGTABLE].valueAsText,
            'table_soil_vegetation_code': parameters[PARAMETER_SOILVEGTABLE_CODE].valueAsText,
            'stream': parameters[PARAMETER_STREAM].valueAsText,
            'table_stream_shape': parameters[PARAMETER_STREAMTABLE].valueAsText,
            'table_stream_shape_code': parameters[PARAMETER_STREAMTABLE_CODE].valueAsText,
            'output': parameters[PARAMETER_PATH_TO_OUTPUT_DIRECTORY].valueAsText,
        }
