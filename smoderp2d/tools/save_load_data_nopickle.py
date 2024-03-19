#!/usr/bin/python

# list blbne
# chce ho rozlisit na int a float
# true false blbne


import numpy as np
import os
import sys
import zipfile

from tools import SaveItems


# Class to load items of different types
class LoadItems:

    def loadlist(self, int_):

        if int_:
            el = self.__int
        else:
            el = self.__float

        nLinesList = self.lines[1].replace('\n', '').split(';')
        nLinesList = int(nLinesList[0])

        line = []

        for i in self.lines[2:]:
            line.append(i.replace('\n', '').split(';'))

        nRec = len(line)

        iLine = 0
        iRec = 0

        list_ = []
        wrk = []

        while iRec < (nRec - 1):
            if int(line[iRec][0]) > iLine:
                list_.append([])
                iLine += 1

            else:
                if int(line[iRec][0]) == iLine:
                    wrk.append(el(line[iRec][1]))

                if int(line[iRec + 1][0]) > iLine:
                    if len(wrk) == 1:
                        list_.append(wrk[0])
                    else:
                        list_.append(wrk)
                    wrk = []
                    iLine += 1
                iRec += 1

        if int(line[iRec][0]) == nLinesList - 1:
            wrk.append(el(line[iRec][1]))
            if len(wrk) == 1:
                list_.append(wrk[0])
            else:
                list_.append(wrk)

        if int(line[iRec][0]) < nLinesList - 1:
            for i in range(nLinesList - int(line[iRec][0]) - 1):
                list_.append([])

        return list_

    def loadint(self):
        n = self.lines[1].replace('\n', '').split(' ')
        return int(n[0])

    def loadfloat(self):
        n = self.lines[1].replace('\n', '').split(' ')
        return float(n[0])

    def loadstr(self):
        n = self.lines[1].replace('\n', '').split(' ')
        return n[0]

    def loadunicode(self):
        n = self.lines[1].replace('\n', '').split(' ')
        return n[0]

    def loadnpy(self):
        rows = self.lines[2:]
        n = len(rows)
        m = len(self.lines[2].split(';'))
        type_ = self.lines[1]
        arr = np.zeros([n, m], float)

        if 'int' in type_:
            self.npyel = self.__int
        if 'float' in type_:
            self.npyel = self.__float

        for i, line in enumerate(rows):
            for j, el in enumerate(line.split(';')):
                arr[i, j] = self.npyel(el)

        return arr

    @staticmethod
    def __float(el):
        return float(el)

    @staticmethod
    def __int(el):
        return int(el)


# Class to save and load the
#  data returned from the datapreparation
#  in and from zip archive
class SaveLoad(SaveItems, LoadItems):

    def load(self, zipfname):
        import shutil

        dir_ = './.save/'
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        if '.zip' in zipfname:
            pass
        else:
            zipfname += '.zip'

        fh = open(sys.argv[1], 'rb')
        z = zipfile.ZipFile(fh)
        for name in z.namelist():
            outpath = "./"
            z.extract(name, outpath)
        fh.close()

        self.countList = 1
        fs = sorted(os.listdir(dir_))
        listOut = []
        for fi in fs:
            with open(dir_ + os.sep + fi, 'r') as f:
                self.lines = f.readlines()
            listOut.append(self.load_item())

        shutil.rmtree(dir_)

        return listOut

    def load_item(self):
        if self.lines[0].replace('\n', '') == str(type(list())):
            if self.countList in [1, 2, 3, 4, 5, 8]:
                self.countList += 1
                return self.loadlist(int_=True)

            else:
                self.countList += 1
                return self.loadlist(int_=False)

        if self.lines[0].replace('\n', '') == str(type(float())):
            return self.loadfloat()
        if self.lines[0].replace('\n', '') == str(type(str())):
            return self.loadstr()
        if self.lines[0].replace('\n', '') == str(type(np.ones([2]))):
            return self.loadnpy()
        if self.lines[0].replace('\n', '') == str(type(unicode)):
            return self.loadunicode()
        if self.lines[0].replace('\n', '') == str(type(int())):
            return self.loadint()


"""
#sl = SaveLoad()

#sl.save(dataList,sys.argv[1])

#del dataList

#dataList = sl.load(sys.argv[1])

"""
