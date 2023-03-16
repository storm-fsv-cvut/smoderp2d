import os

from smoderp2d import ArcGisRunner
from dpre_utils import perform_dpre_ref_test, data_dir, output_dir

def dpre_params():
    return {
        # parameter indexes from the bin/arcgis/SMODERP2D.pyt tool for ArcGIS
        'elevation': os.path.join(data_dir, "dem10m"),
        'soil': os.path.join(data_dir, "soils.shp"),
        'soil_type': "SID",
        'vegetation': os.path.join(data_dir, "landuse.shp"),
        'vegetation_type': "LandUse",
        'rainfall_file': os.path.join(data_dir, "rainfall.txt"),
        'maxdt': 30,
        'end_time': 40,  # convert input to seconds #ML: why?
        'points': os.path.join(data_dir, "points.shp"),
        'table_soil_vegetation': os.path.join(data_dir, "soil_veg_tab_mean.dbf"),
        'table_soil_vegetation_code': "soilveg",
        'streams': os.path.join(data_dir, "stream.shp"),
        'channel_properties_table': os.path.join(data_dir, "stream_shape.dbf"),
        'streams_channel_shape_code': "channel_id",
        'output': output_dir,
    }

if __name__ == "__main__":
    perform_dpre_ref_test(ArcGisRunner, dpre_params, dataprep_only=True)
