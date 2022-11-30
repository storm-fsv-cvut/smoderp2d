import arcpy
import os
import locale
import numpy

class SMODERP2Dtools(object):
    def __init__(self):
        """Set of tools for preparation and executing the SMODERP2D soil erosion model"""
        self.label = "SMODERP2D tools"
        self.alias = ""
        self.description = "Set of tools for executing the SMODERP2D soil erosion model\nDepartment of Irrigation, Drainage and Landscape Engineering\nFaculty of Civil Engineering, Czech Technical University. 2016"

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
       outDir = arcpy.Parameter(
           displayName="Output folder",
           name="outDir",
           datatype="DEWorkspace",
           parameterType="Required",
           direction="Input"
       )
       outDir.filter.list = ["File System"]

       soilvegPropertiesTable = arcpy.Parameter(
           displayName="Soils and Landuse parameters table",
           name="soilvegPropertiesTable",
           datatype="GPTableView",
           parameterType="Required",
           direction="Input"
       )
       soilvegIDfieldName = arcpy.Parameter(
           displayName="Field with the landuse type identifier",
           name="LUtypeFieldName",
           datatype="Field",
           parameterType="Required",
           direction="Input",
       )
       soilvegIDfieldName.parameterDependencies = [soilvegPropertiesTable.name]

       reachFeatures = arcpy.Parameter(
           displayName="Reach feature layer",
           name="reachFeatures",
           datatype="GPFeatureLayer",
           parameterType="Optional",
           direction="Input"
       )
       reachTable = arcpy.Parameter(
           displayName="Reach shapes table",
           name="reachTable",
           datatype="GPTableView",
           parameterType="Optional",
           direction="Input"
       )
       reachIDfieldName = arcpy.Parameter(
           displayName="Field with the reach feature identifier",
           name="reachIDfieldName",
           datatype="Field",
           parameterType="Optional",
           direction="Input",
       )
       reachTable.parameterDependencies = [reachTable.name]

       dataprepOnly = arcpy.Parameter(
           displayName="Do the data preparation only",
           name="dataprepOnly",
           datatype="GPBoolean",
           parameterType="Optional",
           direction="Input",
       )
       dataprepOnly.value = True

       params = [inputSurfaceRaster, inputSoilPolygons, soilTypefieldName, inputLUPolygons, LUtypeFieldName, inputRainfall, maxTimeStep, totalRunTime, inputPoints, outDir,
                 soilvegPropertiesTable, soilvegIDfieldName, reachFeatures, reachTable, reachIDfieldName, dataprepOnly]
       return params

   def updateParameters(self, parameters):
       """Modify the values and properties of parameters before internal validation is performed.  This method is called whenever a parameter has been changed.#"""

       return

   def updateMessages(self, parameters):
       """Modify the messages created by internal validation for each tool parameter.  This method is called after internal validation.#"""

       return

   def execute(self, parameters, messages):
       """The source code of the tool."""

       return