import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dpre_utils import perform_dpre_ref_test, data_dir, output_dir
from smoderp2d import GrassGisRunner

def dpre_params():
    return {
        'elevation': "dem10m@PERMANENT",
        'soil': "soils@PERMANENT",
        'soil_type': "SID",
        'vegetation': "landuse@PERMANENT",
        'vegetation_type': "LandUse",
        'rainfall_file': os.path.join(data_dir, "rainfall.txt"),
        'maxdt': 30,
        'end_time': 40,  # convert input to seconds #ML: why?
        'points': "points@PERMANENT",
        'output': output_dir,
        'table_soil_vegetation': "soil_veg_tab_mean@PERMANENT",
        'table_soil_vegetation_code': "soilveg",
        'stream': "stream@PERMANENT",
        'table_stream_shape': "stream_shape@PERMANENT",
        'table_stream_shape_code': "smoderp"
    }

if __name__ == "__main__":
    perform_dpre_ref_test(GrassGisRunner, dpre_params, dataprep_only=True)
