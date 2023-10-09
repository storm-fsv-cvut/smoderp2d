import os

import numpy as np

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


# Class to save item of different types
class SaveItems:

    def savelist(self, l):
        a = 0
        b = []
        self.f.writelines(str(len(l)) + '\n')
        for i in range(len(l)):
            if not l[i]:
                pass
            else:
                if isinstance(l[i], list):
                    for j in range(len(l[i])):
                        b.append([a, l[i][j]])
                else:
                    b.append([a, l[i]])
            a += 1
        for item1 in b:
            line = ''
            for item2 in item1:
                line += str(item2) + ';'
            line = line[:-1]
            self.f.writelines(line + '\n')

    def saveint(self, f):
        self.f.writelines(str(f) + '\n')

    def savefloat(self, f):
        self.f.writelines(str(f) + '\n')

    def savestr(self, s):
        self.f.writelines(s + '\n')

    def saveunicode(self, uni):
        self.f.writelines(uni + '\n')

    def savenumpy(self, npa):
        type_ = str(type(npa[0][0]))
        self.f.writelines(type_ + '\n')
        if 'int' in type_:
            np.savetxt(self.f, npa, fmt='%15d', delimiter=';')
        if 'float' in type_:
            np.savetxt(self.f, npa, fmt='%15.10e', delimiter=';')
