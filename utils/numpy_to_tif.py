#!/usr/bin/env python3

import sys
import argparse

import numpy as np

from osgeo import gdal

# https://here.isnew.info/how-to-save-a-numpy-array-as-a-geotiff-file-using-gdal.html
def write_geotiff(filename, arr):
    if arr.dtype == np.float32:
        arr_type = gdal.GDT_Float32
    else:
        arr_type = gdal.GDT_Int32

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(filename, arr.shape[1], arr.shape[0], 1, arr_type)
    band = out_ds.GetRasterBand(1)
    band.WriteArray(arr)
    band.FlushCache()
    band.ComputeStatistics(False)

def load_array(filename):
    return np.loadtxt(filename)

def main(filename):
    write_geotiff(filename + '.tif', load_array(filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert numpy array to geofiff file.')

    parser.add_argument('--data',
                        metavar='FILE',
                        type=str,
                        required=True,
                        help='input data file')
    args = parser.parse_args()

    sys.exit(main(args.data))

    
