import os
import sys
import numpy as np
from smoderp2d.core.general import Globals, GridGlobals

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
    rr, rc = GridGlobals.get_region_dim()
    arr = np.zeros(np.shape(surArr), float)
    arrrill = np.zeros(np.shape(surArr), float)
    for i in rr:
        for j in rc[i]:
            arr[i][j] = surArr[i][j].h_sheet_new

    outName = output + os.sep + 'prubeh' + \
        os.sep + str(int(t)).zfill(10) + 'h' + ".asc"
    make_ASC_raster(outName, arr)


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
    make_ASC_raster(outName, arr)
    
def make_ASC_raster(name_, numpy_arr):

    gl = Globals()

    rr, rc = GridGlobals.get_region_dim()
    br = GridGlobals.br
    bc = GridGlobals.bc
    nrows = GridGlobals.r
    ncols = GridGlobals.c

    tmpStr = str(numpy_arr.dtype)[0:3]
    if tmpStr == 'int':
        noData = GridGlobals.NoDataInt
    else:
        noData = GridGlobals.NoDataValue

    tmp = np.copy(numpy_arr)
    tmp.fill(noData)

    f = open(name_, 'w')
    f.write("ncols " + str(ncols) + '\n')
    f.write("nrows " + str(nrows) + '\n')
    f.write("xllcorner " + str(GridGlobals.xllcorner) + '\n')
    f.write("yllcorner " + str(GridGlobals.yllcorner) + '\n')
    f.write("cellsize " + str(GridGlobals.dx) + '\n')
    f.write("nodata_value " + str(noData) + '\n')

    for i in rr:
        for j in rc[i]:
            tmp[i][j] = numpy_arr[i][j]

    # for i in br:
        # for j in bc[i]:
            # tmp[i][j] = numpy_arr[i][j]

    for i in range(nrows):
        line = ""
        for j in range(ncols):
            line += str(tmp[i][j]) + "\t"
        line += '\n'
        f.write(line)
