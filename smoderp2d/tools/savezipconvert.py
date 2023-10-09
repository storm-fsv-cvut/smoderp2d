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
import zipfile

from tools import SaveItems


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
            with open(dir_ + os.sep + "%02d" % id_, 'w') as self.f:
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
        print("converting ", save.ljust(32), " to ", zipn, "...")
        f = open(save, 'r')
        dataList = pickle.load(f)
        sl.save(dataList, zipn)
