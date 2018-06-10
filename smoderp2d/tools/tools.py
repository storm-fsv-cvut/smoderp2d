import os
import sys
import numpy as np
import smoderp2d.constants as constants

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
# Creates a ascii raster from the numpy array
#


def make_ASC_raster(name_, numpy_arr, G):
    rr = G.rr
    rc = G.rc
    br = G.br
    bc = G.bc
    nrows = G.r
    ncols = G.c

    tmpStr = str(numpy_arr.dtype)[0:3]
    if tmpStr == 'int':
        noData = G.NoDataInt
    else:
        noData = G.NoDataValue

    tmp = np.copy(numpy_arr)
    tmp.fill(noData)

    f = open(name_, 'w')
    f.write("ncols " + str(ncols) + '\n')
    f.write("nrows " + str(nrows) + '\n')
    f.write("xllcorner " + str(G.xllcorner) + '\n')
    f.write("yllcorner " + str(G.yllcorner) + '\n')
    f.write("cellsize " + str(G.dx) + '\n')
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


# Returns input parameter from the sys.argv
#


def get_argv(id_):
    iid_ = id_
    # print '!!!Bacha tools.get_argv jsou plus 1!!!';
    iid_ += 1
    return sys.argv[iid_]


def set_argv(id_, value):
    iid_ = id_
    # print '!!!Bacha tools.get_argv jsou plus 1!!!';
    iid_ += 1
    print sys.argv[iid_]
    sys.argv[iid_] = value


def prt_sys_argv():
    for item in sys.argv:
        print item


# Transfers string 'true'/'false' in sys.argv to a logical True/False
#
def logical_argv(id_):
    iid_ = id_
    # print '!!!Bacha tools.get_argv jsou plus 1!!!';
    iid_ += 1
    if isinstance(sys.argv[iid_], str):
        if sys.argv[iid_].lower().strip() == 'true':
            sys.argv[iid_] = True
        elif sys.argv[iid_].lower().strip() == 'false':
            sys.argv[iid_] = False
        else:
            sys.exit('Logical parameter are not assign correctly...')
    if isinstance(sys.argv[iid_], int):
        sys.exit('Logical parameter are not assign correctly...')
    if isinstance(sys.argv[iid_], float):
        sys.exit('Logical parameter are not assign correctly...')
