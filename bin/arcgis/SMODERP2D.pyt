# -*- coding: utf-8 -*-

import arcpy
import sys
import os

from importlib import reload

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..")) # To be removed when building Toolbox package
from smoderp2d.runners.arcgis import ArcGisRunner
from smoderp2d.providers.base import WorkflowMode
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
PARAMETER_POINTS_ID = 9
PARAMETER_SOILVEGTABLE = 10
PARAMETER_SOILVEGTABLE_TYPE = 11
PARAMETER_STREAM = 12
PARAMETER_CHANNEL_TYPE = 13
PARAMETER_CHANNEL_PROPS_TABLE = 14
PARAMETER_FLOW_DIRECTION = 15
PARAMETER_GENERATE_TEMPDATA = 16
PARAMETER_PATH_TO_OUTPUT_DIRECTORY = 17
PARAMETER_WAVE_TYPE = 18

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
        inputSoilPolygons.filter.list = ["Polygon"]

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
        inputLUPolygons.filter.list = ["Polygon"]

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
           category="Computation options"
        )
        maxTimeStep.value = 30

        totalRunTime = arcpy.Parameter(
           displayName="Total running time [min]",
           name="totalRunTime",
           datatype="GPDouble",
           parameterType="Optional",
           direction="Input",
           category="Computation options"
        )
        totalRunTime.value = 40

        inputPoints = arcpy.Parameter(
           displayName="Input points feature layer",
           name="inputPoints",
           datatype="GPFeatureLayer",
           parameterType="Optional",
           direction="Input"
        )
        inputPoints.filter.list = ["Point"]

        inputPointsFieldName = arcpy.Parameter(
           displayName="Field with the input points identifier",
           name="inputPointsFieldName",
           datatype="Field",
           parameterType="Optional",
           direction="Input"
        )
        inputPointsFieldName.parameterDependencies = [inputPoints.name]

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

        streamChannelShapeIDfieldName = arcpy.Parameter(
           displayName="Field with the channel type identifier",
           name="streamChannelShapeIDfieldName",
           datatype="Field",
           parameterType="Optional",
           direction="Input",
        )
        streamChannelShapeIDfieldName.parameterDependencies = [streamNetwork.name]

        channelPropertiesTable = arcpy.Parameter(
           displayName="Channel properties table",
           name="channelTypesTable",
           datatype="GPTableView",
           parameterType="Optional",
           direction="Input"
        )

        outDir = arcpy.Parameter(
           displayName="Output folder",
           name="outDir",
           datatype="DEWorkspace",
           parameterType="Required",
           direction="Input"
        )
        outDir.filter.list = ["File System"]

        flowRoutingType = arcpy.Parameter(
            displayName = "Flow routing algorithm",
            name = "flowRoutingType",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            category = "Advanced"
            )
        flowRoutingType.value = "single"
        flowRoutingType.filter.type = "ValueList"
        flowRoutingType.filter.list = ["single", "multiple"]

        waveType = arcpy.Parameter(
            displayName = "Wave type",
            name = "waveType",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            category = "Advanced"
            )
        waveType.value = "kinematic"
        waveType.filter.type = "ValueList"
        waveType.filter.list = ["kinematic", "diffusion"]

        generateTempData = arcpy.Parameter(
            displayName = "Generate also temporary data",
            name = "generateTempData",
            datatype = "GPBoolean",
            parameterType = "Optional",
            direction = "Input",
            category = "Advanced"
            )
        generateTempData.value = False

        return [
            inputSurfaceRaster, inputSoilPolygons, soilTypefieldName,
            inputLUPolygons, LUtypeFieldName, inputRainfall,
            maxTimeStep, totalRunTime, inputPoints, inputPointsFieldName,
            soilvegPropertiesTable, soilvegIDfieldName, streamNetwork, streamChannelShapeIDfieldName,
            channelPropertiesTable, flowRoutingType, generateTempData, outDir, waveType
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
            'soil_type_fieldname': parameters[PARAMETER_SOIL_TYPE].valueAsText,
            'vegetation': parameters[PARAMETER_VEGETATION].valueAsText,
            'vegetation_type_fieldname': parameters[PARAMETER_VEGETATION_TYPE].valueAsText,
            'rainfall_file': parameters[PARAMETER_PATH_TO_RAINFALL_FILE].valueAsText,
            'maxdt': float(parameters[PARAMETER_MAX_DELTA_T].valueAsText),
            'end_time': float(parameters[PARAMETER_END_TIME].valueAsText),
            'points': parameters[PARAMETER_POINTS].valueAsText,
            'points_fieldname': parameters[PARAMETER_POINTS_ID].valueAsText,
            'table_soil_vegetation': parameters[PARAMETER_SOILVEGTABLE].valueAsText,
            'table_soil_vegetation_fieldname': parameters[PARAMETER_SOILVEGTABLE_TYPE].valueAsText,
            'streams': parameters[PARAMETER_STREAM].valueAsText,
            'streams_channel_type_fieldname': parameters[PARAMETER_CHANNEL_TYPE].valueAsText,
            'channel_properties_table': parameters[PARAMETER_CHANNEL_PROPS_TABLE].valueAsText,
            'flow_direction': parameters[PARAMETER_FLOW_DIRECTION].valueAsText,
            'generate_temporary': parameters[PARAMETER_GENERATE_TEMPDATA].value,
            'output': parameters[PARAMETER_PATH_TO_OUTPUT_DIRECTORY].valueAsText,
            'wave': parameters[PARAMETER_WAVE_TYPE].valueAsText,
        }
