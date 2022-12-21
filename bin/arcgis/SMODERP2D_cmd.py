import os
import sys

import arcpy

from smoderp2d import ArcGisRunner, Logger
from smoderp2d.exceptions import ProviderError

def run_smoderp2d(parameters):
    try:
        runner = ArcGisRunner()

        runner.set_options(parameters)
        # if flags['d']:
        #     runner.set_comptype(
        #         comp_type=CompType.dpre,
        #         data_file=options['pickle_file']
        # )

        runner.run()
    except ProviderError as e:
        sys.exit(e)

if __name__ == "__main__":
    arcpy.env.workspace = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "data")

    output_dir = os.path.join(arcpy.env.workspace, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    parameters = {
        # parameter indexes from the bin/arcgis/SMODERP2D.pyt tool for ArcGIS
        'elevation': os.path.join(arcpy.env.workspace, "dem10m"),
        'soil': os.path.join(arcpy.env.workspace, "soils.shp"),
        'soil_type': "SID",
        'vegetation': os.path.join(arcpy.env.workspace, "landuse.shp"),
        'vegetation_type': "LandUse",
        'rainfall_file': os.path.join(arcpy.env.workspace, "rainfall.txt"),
        'maxdt': 30,
        'end_time': 40 * 60.0,  # convert input to seconds
        'points': os.path.join(arcpy.env.workspace, "points.shp"),
        'output': output_dir,
        'table_soil_vegetation': os.path.join(arcpy.env.workspace, "soil_veg_tab_mean.dbf"),
        'table_soil_vegetation_code': "soilveg",
        'stream': None,
        'table_stream_shape': None,
        'table_stream_shape_code': None
    }

    run_smoderp2d(parameters)
