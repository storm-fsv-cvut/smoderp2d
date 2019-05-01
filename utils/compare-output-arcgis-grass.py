#!/usr/bin/env python

# http://geo102.fsv.cvut.cz/~landa/tmp/smoderp_arcgis_output.zip

import os
import sys

from osgeo import gdal, ogr

import grass.script as gs

def comp_rasters(directory, cleanup=False, png=False):
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        if not os.path.isdir(path) or path.endswith('gdb'):
            continue
        ds = gdal.Open(path)
        if ds is None:
            continue

        # blacklist
        if item in ['fl_dir']:
            continue

        # link arcgis raster to GRASS
        arcgis = '{}_arcgis'.format(item)
        gs.run_command('r.external',
                       input=path, output=arcgis, flags='o'
        )
        gs.run_command('r.colors',
                       map=arcgis, raster=item
        )

        gs.run_command('g.region',
                       raster=item
        )
        diff = '{}_diff'.format(item)
        gs.run_command('r.mapcalc',
                       expression='{} = {} - {}'.format(diff, arcgis, item)
        )
        gs.run_command('r.colors',
                       map=diff, color='diff'
        )
        if png:
            gs.run_command('d.mon',
                           start='cairo', output=os.path.join(OUTPUT, '{}.png'.format(item))
            )
            gs.run_command('d.rast.leg',
                           map=diff
            )
            gs.run_command('d.mon',
                           stop='cairo'
            )
        print('{sep}{nl}{map}{nl}{sep}{nl}'.format(sep='-' * 80, nl=os.linesep, map=item))
        stats = gs.parse_command('r.univar',
                                 flags='g',
                                 map=diff
        )
        for key in ('min', 'max', 'range'):
            print ('{}={}'.format(key, stats[key]))
        if float(stats['range']) < 1e-7:
            print ("-> OK")
        else:
            print ("-> KO")
        if cleanup:
            gs.run_command('g.remove',
                           type='raster', name=','.join(arcgis, diff), flags='f'
            )

def comp_vectors(directory):
    ds = ogr.Open(directory)
    for i in range(ds.GetLayerCount()):
        lyr = ds.GetLayer(i)
        name = lyr.GetName()

        # TODO: what to compare ?

if __name__ == "__main__":
    ARCGIS_OUTPUT = os.path.join(os.environ['HOME'], 'Downloads', 'output')
    if not os.path.exists(ARCGIS_OUTPUT):
        if len(sys.argv) > 1:
            ARCGIS_OUTPUT = sys.argv[1]
        else:
            sys.exit("Provide path to ArcGIS data dir")

    OUTPUT=os.path.join(ARCGIS_OUTPUT, 'diff')
    if not os.path.exists(OUTPUT):
        os.makedirs(OUTPUT)
    os.environ['GRASS_VERBOSE'] = '0'
    os.environ['GRASS_OVERWRITE'] = '1'

    # data preparation
    comp_rasters(os.path.join(ARCGIS_OUTPUT, 'temp'))
    # comp_rasters(os.path.join(ARCGIS_OUTPUT, 'stream_prep'))
    # comp_vectors(os.path.join(ARCGIS_OUTPUT, 'temp', 'tempGDB.gdb'))
    # comp_vectors(os.path.join(ARCGIS_OUTPUT, 'stream_prep', 'stream_prep.gdb'))
