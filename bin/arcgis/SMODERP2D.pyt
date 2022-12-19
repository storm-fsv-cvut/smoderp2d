# -*- coding: utf-8 -*-

import arcpy
import sys
import os
import locale
import numpy
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
PARAMETER_PATH_TO_OUTPUT_DIRECTORY = 9

PARAMETER_SOILVEGTABLE = 10
PARAMETER_SOILVEGTABLE_CODE = 11
PARAMETER_STREAM = 12
PARAMETER_STREAMTABLE = 13
PARAMETER_STREAMTABLE_CODE = 14
PARAMETER_DPRE_ONLY = 15

class Toolbox(object):
    def __init__(self):
        """Set of tools for preparation and executing the SMODERP2D soil erosion model"""
        self.label = "SMODERP2D tools"
        self.alias = ""
        self.description = "Set of tools for executing the SMODERP2D soil erosion model\nDepartment of Irrigation, Drainage and Landscape Water Management\nFaculty of Civil " \
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

        self.processignGDBname = "processing.gdb"
        self.AIO_outline = None

        self.dem_slope = None
        self.dem_fill = None
        self.dem_flowdir = None
        self.dem_flowacc = None
        self.dem_aspect = None

        self.dem_aoi = None
        self.dem_slope_aoi = None
        self.dem_flowacc_aoi = None
        self.dem_aspect_aoi = None

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
           name="soilvegIDfieldName",
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
        """Values and properties of parameters before internal validation is performed.  This method is called whenever a parameter has been changed.#"""
        arcpy.env.workspace = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "data")
        parameters[PARAMETER_DEM].value = "dem10m"
        parameters[PARAMETER_SOIL].value = "soils.shp"
        parameters[PARAMETER_SOIL_TYPE].value = "SID"
        parameters[PARAMETER_VEGETATION].value = "landuse.shp"
        parameters[PARAMETER_VEGETATION_TYPE].value = "LandUse"
        parameters[PARAMETER_PATH_TO_RAINFALL_FILE].value = "rainfall.txt"
        parameters[PARAMETER_MAX_DELTA_T].value = 30
        parameters[PARAMETER_END_TIME].value = 40
        parameters[PARAMETER_POINTS].value = "points.shp"
        # parameters[PARAMETER_PATH_TO_OUTPUT_DIRECTORY].value = "output"
        parameters[PARAMETER_SOILVEGTABLE].value = "soil_veg_tab_mean.dbf"
        parameters[PARAMETER_SOILVEGTABLE_CODE].value = "soilveg"
        # parameters[PARAMETER_STREAM].value =
        # parameters[PARAMETER_STREAMTABLE].value =
        # parameters[PARAMETER_STREAMTABLE_CODE].value =

    def updateMessages(self, parameters):
        """Messages created by internal validation for each tool parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        import smoderp2d
        reload(smoderp2d) # remove when finished ...

        try:
            runner = smoderp2d.ArcGisRunner()

            runner.set_options(self._get_input_params(parameters))
            # if flags['d']:
            #     runner.set_comptype(
            #         comp_type=CompType.dpre,
            #         data_file=options['pickle_file']
            # )

            runner.run()
        except ProviderError as e:
            # gs.fatal(e)
            # arcpy....
            pass

        #self.calculate_AOI_outline()
        #self.calculate_DEM_products()
        #self.clip_DEM_products()

        return

    @staticmethod
    def _get_input_params(parameters):
        """Get input parameters from ArcGIS toolbox.
        """
        return {
            # parameter indexes from the bin/arcgis/SMODERP2D.pyt tool for ArcGIS
            'elevation': parameters[PARAMETER_DEM].valueAsText,
            'soil': parameters[PARAMETER_SOIL].valueAsText,
            'soil_type': parameters[PARAMETER_SOIL_TYPE].valueAsText,
            'vegetation': parameters[PARAMETER_VEGETATION].valueAsText,
            'vegetation_type': parameters[PARAMETER_VEGETATION_TYPE].valueAsText,
            'rainfall_file': parameters[PARAMETER_PATH_TO_RAINFALL_FILE].valueAsText,
            'maxdt': float(parameters[PARAMETER_MAX_DELTA_T].valueAsText),
            'end_time': float(parameters[PARAMETER_END_TIME].valueAsText) * 60.0,  # convert input to seconds
            'points': parameters[PARAMETER_POINTS].valueAsText,
            'output': parameters[PARAMETER_PATH_TO_OUTPUT_DIRECTORY].valueAsText,
            'table_soil_vegetation': parameters[PARAMETER_SOILVEGTABLE].valueAsText,
            'table_soil_vegetation_code': parameters[PARAMETER_SOILVEGTABLE_CODE].valueAsText,
            'stream': parameters[PARAMETER_STREAM].valueAsText,
            'table_stream_shape': parameters[PARAMETER_STREAMTABLE].valueAsText,
            'table_stream_shape_code': parameters[PARAMETER_STREAMTABLE_CODE].valueAsText
        }



    # def calculate_AOI_outline(self):
    #     #dem_mask = self.storage.output_filepath('dem_mask')
    #     dem_mask_path = os.path.join(self.processingGDBpath, "dem_mask")
    #     dem_mask = arcpy.sa.Reclassify( self._input_params['elevation'], "VALUE", "-100000 100000 1", "DATA")
    #     dem_mask.save(dem_mask_path)
    #     #dem_polygon = os.path.join(self.data['temp'], 'dem_outline')
    #     dem_polygon = os.path.join(self.processingGDBpath, "dem_polygon")
    #     arcpy.conversion.RasterToPolygon(dem_mask, dem_polygon, "NO_SIMPLIFY", "VALUE")
    #
    #     #dem_soil_veg_intersection = os.path.join(self.data['temp'], 'AOI')
    #     dem_soil_veg_intersection = os.path.join(self.processingGDBpath, "veg_soil_AOI")
    #     arcpy.analysis.Intersect([dem_polygon, self._input_params['soil'], self._input_params['vegetation']], dem_soil_veg_intersection, "NO_FID")
    #
    #     AOI_outline = os.path.join(self.processingGDBpath, "AOI")
    #     arcpy.management.Dissolve(dem_soil_veg_intersection, AOI_outline)
    #
    #     self.AIO_outline = AOI_outline
    #     return

    # def calculate_DEM_products(self):
    #     # calculate the depressionless DEM
    #     if not self.dem_fill:
    #         dem_fill_path = os.path.join(self.processingGDBpath, "dem_fill")
    #         dem_fill = arcpy.sa.Fill(self._input_params['elevation'])
    #         dem_fill.save(dem_fill_path)
    #         self.dem_fill = dem_fill_path
    #
    #     # calculate the flow direction
    #     if not self.dem_flowacc:
    #         if not self.dem_flowdir:
    #             dem_flowdir_path = os.path.join(self.processingGDBpath, "dem_flowdir")
    #             flowdir = arcpy.sa.FlowDirection(self.dem_fill)
    #             flowdir.save(dem_flowdir_path)
    #             self.dem_flowdir = dem_flowdir_path
    #
    #         dem_flowacc_path = os.path.join(self.processingGDBpath, "dem_flowacc")
    #         flowacc = arcpy.sa.FlowAccumulation(self.dem_flowdir)
    #         flowacc.save(dem_flowacc_path)
    #         self.dem_flowacc = dem_flowacc_path
    #
    #     # calculate slope
    #     if not self.dem_slope:
    #         dem_slope_path = os.path.join(self.processingGDBpath, "dem_slope")
    #         dem_slope = arcpy.sa.Slope(self.dem_fill, "PERCENT_RISE", 1)
    #         dem_slope.save(dem_slope_path)
    #         self.dem_slope = dem_slope_path
    #
    #     # calculate aspect
    #     if not self.dem_aspect:
    #         dem_aspect_path = os.path.join(self.processingGDBpath, "dem_aspect")
    #         dem_aspect = arcpy.sa.Aspect(self.dem_fill, "", "")
    #         dem_aspect.save(dem_aspect_path)
    #         self.dem_aspect = dem_aspect_path
    #     return

    def clip_DEM_products(self):
        # clip DEM
        if not self.dem_aoi:
            dem_aoi_path = os.path.join(self.processingGDBpath, "dem_aoi")
            self.dem_aoi = arcpy.management.Clip(self.dem_fill, "", dem_aoi_path, self.AIO_outline, "", "ClippingGeometry")

        # clip the flow direction
        if self.dem_flowacc and not self.dem_flowacc_aoi:
            flowacc_aoi_path = os.path.join(self.processingGDBpath, "dem_flowacc_aoi")
            self.dem_flowacc_aoi = arcpy.management.Clip(self.dem_flowacc, "", flowacc_aoi_path, self.AIO_outline, "", "ClippingGeometry")

        # clip the slope
        if self.dem_slope and not self.dem_slope_aoi:
            slope_aoi_path = os.path.join(self.processingGDBpath, "dem_slope_aoi")
            self.dem_slope_aoi = arcpy.management.Clip(self.dem_slope, "", slope_aoi_path, self.AIO_outline, "", "ClippingGeometry")

        # calculate aspect
        if self.dem_aspect and not self.dem_aspect_aoi:
            aspect_aoi_path = os.path.join(self.processingGDBpath, "dem_aspect_aoi")
            self.dem_slope_aoi = arcpy.management.Clip(self.dem_aspect, "", aspect_aoi_path, self.AIO_outline, "", "ClippingGeometry")
        return
