#!/usr/bin/python


# samostatny skript na konvert save souboru
# do zipu, aby mohl byt nacten
# s novou very, ktera je bez pickle
# v podtate to same jako u
# /tools/save_load_data_nopickle.py
# bez naciracich metod


import pickle
import numpy as np
import os
import sys
import zipfile
import time


class SaveItems:

    def savelist(self, l):
        a = 0
        b = []
        self.f.writelines(str(len(l)) + '\n')
        for i in range(len(l)):
            if l[i] == []:
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


class SaveLoad(SaveItems):

    def save(self, data, zipfname):
        import shutil

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
            # print "%02d" % (id_)
            with open(dir_ + os.sep + "%02d" % (id_), 'w') as self.f:
                self.f.writelines(str(type(it)) + '\n')
                self.save_item(it)

        for root, dirs, files in os.walk(dir_):
            for file in files:
                    # print os.path.join(root, file)
                zipf.write(os.path.join(root, file))

        shutil.rmtree(dir_)

    def save_item(self, it):
        if isinstance(it, list):
            # if self.countList in [1,2,3,4,5,8] :
                # print 'int'
            # else:
                # print 'float'
            # print it
            # print
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


sl = SaveLoad()


for file in os.listdir("./"):
    if file.endswith(".save"):
        save = os.path.join("./", file)
        zipn = save.replace(".save", ".zip")
        print "converting ", save.ljust(32), " to ", zipn, "..."
        f = open(save, 'r')
        dataList = pickle.load(f)
        sl.save(dataList, zipn)
