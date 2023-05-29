import os
import sys
import pytest

from test_utils import PerformTest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import GrassGisRunner, Runner

def params():
    return {
        'elevation': "dem10m@PERMANENT",
        'soil': "soils@PERMANENT",
        'vegetation': "landuse@PERMANENT",
        'points': "points@PERMANENT",
        'table_soil_vegetation': "soil_veg_tab_mean@PERMANENT",
        'streams': "stream@PERMANENT",
        'channel_properties_table': "stream_shape@PERMANENT"
    }

class TestGrass:
    def test_001_dpre(self):
        PerformTest(GrassGisRunner, params).run_dpre()

    def test_002_roff(self):
        # TODO: will be solved in separated PR
        # PerformTest(Runner).run_roff(
        #     os.path.join(os.path.dirname(__file__), "gistest.ini")
        # )
        pass

    def test_003_full(self):
        PerformTest(GrassGisRunner, params).run_full()
        
