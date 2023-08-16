import os

# Make an asc raster output from a numpy array
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
    arr = surArr.h
    arrrill = surArr.h_rill

    outName = output + os.sep + 'prubeh' + \
        os.sep + str(int(t)).zfill(10) + 'h' + ".asc"
    make_ASC_raster(outName, arr, G)
    outName = output + os.sep + 'prubeh' + os.sep + \
        str(int(t)).zfill(10) + 'hrill' + ".asc"
    make_ASC_raster(outName, arrrill, G)


def make_state_raster(surArr, G, t):
    arr = surArr.state

    outName = 'state' + str(int(t)).zfill(10) + 'h' + ".asc"
    make_ASC_raster(outName, arr, G)


def make_sub_raster(subArr, G, t, output):
    arr = subArr.h

    outName = output + os.sep + 'prubeh' + \
        os.sep + str(int(t)).zfill(10) + 'hsub' + ".asc"
    make_ASC_raster(outName, arr, G)
