import os
import shutil
import zipfile

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

    def __init__(self):
        self.countList = 1

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

    def save(self, data, zipfname):

        dir_ = './.save/'

        if '.zip' in zipfname:
            pass
        else:
            zipfname += '.zip'

        zipf = zipfile.ZipFile(zipfname, 'w', zipfile.ZIP_DEFLATED)

        self.countList = 1
        if not os.path.exists(dir_):
            os.makedirs(dir_)
        for id_, it in enumerate(data):
            with open(dir_ + os.sep + "%02d" % id_, 'w') as self.f:
                self.f.writelines(str(type(it)) + '\n')
                self.save_item(it)

        for root, _, files in os.walk(dir_):
            for file in files:
                zipf.write(os.path.join(root, file))

        shutil.rmtree(dir_)

    def save_item(self, it):
        if isinstance(it, list):
            self.savelist(it)
            self.countList += 1
        if isinstance(it, float):
            self.savefloat(it)
        if isinstance(it, str):
            self.savestr(it)
        if isinstance(it, np.ndarray):
            self.savenumpy(it)
        if isinstance(it, unicode):
            self.saveunicode(it)
        if isinstance(it, int):
            self.saveint(it)
