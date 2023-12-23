import os
import sys
import pytest
from test_utils import PerformTest, data_dir, class_manager

from smoderp2d.runners.arcgis import ArcGisRunner

def params(reference_dir):
    return {
        'elevation': os.path.join(data_dir, reference_dir, "dem.tif"),
        'soil': os.path.join(data_dir, reference_dir, "soils.shp"),
        'vegetation': os.path.join(data_dir, reference_dir, "landuse.shp"),
        'points': os.path.join(data_dir, reference_dir, "points.shp"),
        'table_soil_vegetation': os.path.join(
            data_dir, reference_dir, "soil_veg_tab.{}".format("dbf" if reference_dir == "nucice" else "csv")
        ),
        'streams': os.path.join(data_dir, reference_dir, "streams.shp"),
        'channel_properties_table':  os.path.join(data_dir, reference_dir, "streams_shape.dbf")
    }

@pytest.mark.usefixtures('class_manager')
class TestArcGis:
    def test_001_dpre(self):
        PerformTest(
            ArcGisRunner, self.reference_dir, params(self.reference_dir)
        ).run_dpre()

    # def test_002_roff(self):
    #     # https://github.com/storm-fsv-cvut/smoderp2d/issues/199
    #     # PerformTest(Runner).run_roff(
    #     #     os.path.join(os.path.dirname(__file__), "gistest.ini")
    #     # )
    #     pass

    # def test_003_full(self):
    #     # PerformTest(ArcGisRunner, params).run_full()
    #     pass
