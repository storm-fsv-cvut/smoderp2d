import os
import sys

from test_utils import PerformTest, data_dir

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import ArcGisRunner


def params():
    return {
        'elevation': os.path.join(data_dir, "nucice", "dem10m.tif"),
        'soil': os.path.join(data_dir, "nucice", "soils.shp"),
        'vegetation': os.path.join(data_dir, "nucice", "landuse.shp"),
        'points': os.path.join(data_dir, "nucice", "points.shp"),
        'table_soil_vegetation': os.path.join(
            data_dir, "nucice", "soil_veg_tab_mean.dbf"
        ),
        'streams': os.path.join(data_dir, "nucice", "stream.shp"),
        'channel_properties_table':  os.path.join(data_dir, "nucice", "stream_shape.dbf")
    }


class TestArcGis:
    def test_001_dpre(self):
        PerformTest(ArcGisRunner, params).run_dpre()

    def test_002_roff(self):
        # https://github.com/storm-fsv-cvut/smoderp2d/issues/199
        # PerformTest(Runner).run_roff(
        #     os.path.join(os.path.dirname(__file__), "gistest.ini")
        # )
        pass

    def test_003_full(self):
        # PerformTest(ArcGisRunner, params).run_full()
        pass
