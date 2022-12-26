import os
import sys
import filecmp

from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import CompType

def _dpre_params():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    output_dir = os.path.join(data_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

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
        'output': output_dir,
        'table_soil_vegetation': os.path.join(data_dir, "soil_veg_tab_mean.dbf"),
        'table_soil_vegetation_code': "soilveg",
        'stream': os.path.join(data_dir, "stream.shp"),
        'table_stream_shape': os.path.join(data_dir, "stream_shape.dbf"),
        'table_stream_shape_code': "smoderp",
        'pickle_file': os.path.join(output_dir, 'dpre.save')
    }

def perform_dpre_ref_test(runner):
    params = _dpre_params()

    try:
        runner = runner()
        runner.set_options(params)
        # run only data preparation
        runner.set_comptype(
            comp_type=CompType.dpre,
            data_file=params['pickle_file']
        )
        runner.run()
    except ProviderError as e:
        sys.exit(e)

    assert filecmp.cmp(
        params['pickle_file'],
        os.path.join(output_dir, '..', 'reference', 'dpre.save')
    ) == True
