#!/bin/bash -e

# grass ../grassdata/smoderp2d-location/PERMANENT/
# ./import_grass.sh

export GRASS_OVERWRITE='1'

r.import -o input=dem10m/w001001.adf output=dem10m
v.import -o input=soils.shp output=soils
v.import -o input=landuse.shp output=landuse
v.import -o input=points.shp output=points
v.import -o input=stream.shp output=stream
db.in.ogr input=soil_veg_tab_mean.dbf output=soil_veg_tab_mean
db.in.ogr input=stream_shape.dbf output=stream_shape

exit 0
