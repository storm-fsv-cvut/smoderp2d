#!/usr/bin/env python3

# grass -c EPSG:5514 /tmp/smoderp2d-location --exec python3 import_grass.py nucice

import os
from pathlib import Path
from grass.pygrass.modules import Module

os.environ['GRASS_OVERWRITE'] ='1'

def do_import(path):
    for rast in Path(path).glob('*.tif'):
        Module('r.import', overwrite=True, input=str(rast), output=rast.stem, flags='o')
    for vect in Path(path).glob('*.shp'):
        Module('v.import', overwrite=True, input=str(vect), output=vect.stem, snap=0.001)
    for tabl in Path(path).glob('*.dbf'):
        if not tabl.with_suffix('.shp').exists():
            Module('db.in.ogr', overwrite=True, input=str(tabl), output=tabl.stem)
    for tabl in Path(path).glob('*.csv'):
        Module('db.in.ogr', overwrite=True, input=str(tabl), output=tabl.stem, gdal_doo="AUTODETECT_TYPE=YES")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog='import_grass',
        description='Import tests into GRASS location')

    parser.add_argument('directory')

    args = parser.parse_args()

    do_import(args.directory)
