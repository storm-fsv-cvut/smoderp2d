#!/bin/sh

# bash ./bin/grass/batch_process.sh
PYTHONPATH=`pwd` python3 ./bin/grass/batch_process.py \
        --elevation ./tests/data/nucice/dem.tif \
        --soil ./tests/data/nucice/soils.shp \
        --soil_type_fieldname Soil \
        --vegetation ./tests/data/nucice/landuse.shp  \
        --vegetation_type_fieldname LandUse \
        --rainfall_file ./tests/data/rainfall_nucice.txt \
        --end_time 5 \
        --maxdt 5 \
        --table_soil_vegetation ./tests/data/nucice/soil_veg_tab.dbf \
        --table_soil_vegetation_fieldname soilveg \
        --output /tmp/smoderp2d \
        --points ./tests/data/nucice/points.shp \
        --points_fieldname point_id \
        --streams ./tests/data/nucice/streams.shp \
        --channel_properties_table ./tests/data/nucice/streams_shape.dbf \
        --streams_channel_type_fieldname channel_id \
        --flow_direction 'single' \
        --wave kinematic \
        --generate_temporary

