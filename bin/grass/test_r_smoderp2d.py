#!/usr/bin/env python3

import os
import subprocess

test_dir = os.path.dirname(__file__)
data_dir = os.path.join(test_dir, '..', '..', 'tests', 'data')
test = subprocess.Popen([
    os.environ['GRASS_PYTHON'],
    os.path.join(test_dir, 'r.smoderp2d', 'r.smoderp2d.py'),
    'elevation=dem10m',
    'soil=soils',
    'soil_type=SID',
    'vegetation=landuse',
    'vegetation_type=LandUse',
    'rainfall_file={}'.format(os.path.join(data_dir, 'rainfall.txt')),
    'points=points',
    'table_soil_vegetation=soil_veg_tab_mean',
    'table_soil_vegetation_code=soilveg',
    'stream=stream',
    'table_stream_shape=stream_shape',
    'table_stream_shape_code=smoderp',
    'maxdt=10',
    'end_time=120',
    'output_dir={}'.format(os.path.join(data_dir, 'output_grass'))
])
test.wait()
