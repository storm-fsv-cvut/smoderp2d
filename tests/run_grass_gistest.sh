#!/bin/sh

if test -z "$1"; then
    echo "Usage: $0 rain_sim|nucice"
    exit 1
fi

k_flag=""
if test -n "$2"; then
    k_flag="-k $2"
fi
LOCATION=/tmp/smoderp2d-$1

rm -rf $LOCATION
grass -c EPSG:5514 $LOCATION --exec python3 tests/data/import_grass.py tests/data/rain_sim

grass -c $LOCATION/test --exec python3 -m pytest tests/test_grass.py -v $k_flag --reference_dir $1

echo "----------------------------------------------------------------"
echo "GRASS location: $LOCATION"
echo "----------------------------------------------------------------"

exit 0
