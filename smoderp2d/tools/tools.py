import os
import sys
import numpy as np

# Make a asc raster output from a numpy array
#
#  only water level in rills and surface are considered
#  this method saves stages of the advancing computation
#  in ascii rasters, not included in the official release
#
#  @param surArr arrays with values
#  @param G Globals parameters
#  @param t time of computing
#  @param output output directory
#
#
def make_sur_raster(surArr, G, t, output):
    rrows = G.rr
    rcols = G.rc
    arr = np.zeros(np.shape(surArr), float)
    arrrill = np.zeros(np.shape(surArr), float)
    for i in rrows:
        for j in rcols[i]:
            arr[i][j] = surArr[i][j].h
            arrrill[i][j] = surArr[i][j].h_rill

    outName = output + os.sep + 'prubeh' + \
        os.sep + str(int(t)).zfill(10) + 'h' + ".asc"
    make_ASC_raster(outName, arr, G)
    outName = output + os.sep + 'prubeh' + os.sep + \
        str(int(t)).zfill(10) + 'hrill' + ".asc"
    make_ASC_raster(outName, arrrill, G)


def make_state_raster(surArr, G, t):
    rrows = G.rr
    rcols = G.rc
    arr = np.zeros(np.shape(surArr), float)
    for i in rrows:
        for j in rcols[i]:
            arr[i][j] = surArr[i][j].state

    outName = 'state' + str(int(t)).zfill(10) + 'h' + ".asc"
    make_ASC_raster(outName, arr, G)


def make_sub_raster(subArr, G, t, output):
    rrows = G.rr
    rcols = G.rc
    arr = np.zeros(np.shape(subArr), float)
    for i in rrows:
        for j in rcols[i]:
            arr[i][j] = subArr[i][j].h

    outName = output + os.sep + 'prubeh' + \
        os.sep + str(int(t)).zfill(10) + 'hsub' + ".asc"
    make_ASC_raster(outName, arr, G)
