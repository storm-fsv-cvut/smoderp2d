import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dpre_utils import perform_dpre_ref_test, data_dir, output_dir
from smoderp2d import GrassGisRunner


def dpre_params():
    return {
        'elevation': "dem10m@PERMANENT",
        'soil': "soils@PERMANENT",
        'soil_type_fieldname': "SID",
        'vegetation': "landuse@PERMANENT",
        'vegetation_type_fieldname': "LandUse",
        'rainfall_file': os.path.join(data_dir, "rainfall.txt"),
        'maxdt': 30,
        'end_time': 40,
        'points': "points@PERMANENT",
        'table_soil_vegetation': "soil_veg_tab_mean@PERMANENT",
        'table_soil_vegetation_fieldname': "soilveg",
        'streams': "stream@PERMANENT",
        'channel_properties_table': "stream_shape@PERMANENT",
        'streams_channel_type_fieldname': "channel_id",
        'output': output_dir,
    }


class TestGrass:
    config_file = os.path.join(os.path.dirname(__file__), "quicktest.ini")

    def test_001_dpre(self):
        perform_dpre_ref_test(GrassGisRunner, dpre_params, dataprep_only=True)
