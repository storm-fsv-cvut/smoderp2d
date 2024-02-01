#!/usr/bin/python


# samostatny skript na konvert save souboru
# do zipu, aby mohl byt nacten
# s novou very, ktera je bez pickle
# v podtate to same jako u
# /tools/save_load_data_nopickle.py
# bez naciracich metod


import pickle
import os

from tools import SaveItems


sl = SaveItems()


for file in os.listdir("./"):
    if file.endswith(".save"):
        save = os.path.join("./", file)
        zipn = save.replace(".save", ".zip")
        print("converting ", save.ljust(32), " to ", zipn, "...")
        f = open(save, 'r')
        dataList = pickle.load(f)
        sl.save(dataList, zipn)
