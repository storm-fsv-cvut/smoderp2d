import os
import sys

from test_utils import PerformTest, data_dir

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import ArcGisRunner

def params():
    return {
        'elevation': os.path.join(data_dir, "dem10m.tif"),
        'soil': os.path.join(data_dir, "soils.shp"),
        'vegetation': os.path.join(data_dir, "landuse.shp"),
        'points': os.path.join(data_dir, "points.shp"),
        'table_soil_vegetation': os.path.join(data_dir, "soil_veg_tab_mean.dbf"),
        'table_soil_vegetation_fieldname': "soilveg",
        'streams': os.path.join(data_dir, "stream.shp"),
        'channel_properties_table':  os.path.join(data_dir, "stream_shape.dbf")
    }

class TestArcGis:
    def test_001_dpre(self):
        PerformTest(ArcGisRunner, params).run_dpre()
