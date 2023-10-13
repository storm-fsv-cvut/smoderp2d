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

from tools import SaveItems


class SaveLoad(SaveItems):

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
