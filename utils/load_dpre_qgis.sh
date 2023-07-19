#!/bin/bash -e

if test -z $1; then
    echo "usage: $0 mat_dem"
    exit 1
fi

filename=$1

dir1=./tests/data/output/dpre.extracted/
dir2=./tests/data/reference/gistest/grass/dpre.extracted/
./utils/numpy_to_tif.py --data $dir1/$filename
./utils/numpy_to_tif.py --data $dir2/$filename

qgis $dir1/$filename.tif $dir2/$filename.tif

