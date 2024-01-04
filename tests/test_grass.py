import os
import sys
import pytest

from test_utils import PerformTest, class_manager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d.runners.grass import GrassGisRunner


def params():
    return {
        'elevation': "dem@PERMANENT",
        'soil': "soils@PERMANENT",
        'vegetation': "landuse@PERMANENT",
        'points': "points@PERMANENT",
        'table_soil_vegetation': "soil_veg_tab@PERMANENT",
        'streams': "streams@PERMANENT",
        'channel_properties_table': "streams_shape@PERMANENT"
    }


@pytest.mark.usefixtures('class_manager')
class TestGrass:
    def test_001_dpre(self):
        PerformTest(GrassGisRunner, self.reference_dir, params()).run_dpre()

    # def test_002_roff(self):
    #     # https://github.com/storm-fsv-cvut/smoderp2d/issues/199
    #     # PerformTest(Runner).run_roff(
    #     #     os.path.join(os.path.dirname(__file__), "gistest.ini")
    #     # )
    #     pass

    def test_002_full(self):
        PerformTest(GrassGisRunner, self.reference_dir, params()).run_full()
