import os
import sys
import pytest
from test_utils import PerformTest, data_dir, class_manager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import ArcGisRunner

def params(dataset):
    return {
        'elevation': os.path.join(data_dir, dataset, "dem.tif"),
        'soil': os.path.join(data_dir, dataset, "soils.shp"),
        'vegetation': os.path.join(data_dir, dataset, "landuse.shp"),
        'points': os.path.join(data_dir, dataset, "points.shp"),
        'table_soil_vegetation': os.path.join(
            data_dir, dataset, "soil_veg_tab.dbf"
        ),
        'streams': os.path.join(data_dir, dataset, "streams.shp"),
        'channel_properties_table':  os.path.join(data_dir, dataset, "streams_shape.dbf")
    }

@pytest.mark.usefixtures('class_manager')
class TestArcGis:
    def test_001_dpre(self):
        PerformTest(ArcGisRunner, params(self.dataset)).run_dpre(self.dataset)

    def test_002_roff(self):
        # https://github.com/storm-fsv-cvut/smoderp2d/issues/199
        # PerformTest(Runner).run_roff(
        #     os.path.join(os.path.dirname(__file__), "gistest.ini")
        # )
        pass

    def test_003_full(self):
        # PerformTest(ArcGisRunner, params).run_full()
        pass
