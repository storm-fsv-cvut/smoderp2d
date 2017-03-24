## @package main_src.tools.save_load_data to safe and load data to with a pickle package
#
#  to safe and load data to with a pickle package

import numpy as np
import os
import pickle


def splitdirfile(dirfile_):
  p = dirfile_.split(os.sep)
  n = len(p)
  file_ = p[n-1]
  dir_  = ''
  for i in range(n-1):
    dir_ = dir_  + p[i] + os.sep
  
  return dir_, file_
  
  
  
def save_data(data,dirfile_):
  dir_, file_ = splitdirfile(dirfile_)
  if not os.path.exists(dir_):
    os.makedirs(dir_)
  with open(dir_ + file_, 'wb') as f:
    pickle.dump(data, f)
  
  
  
  
  
def load_data(dirfile_):     
  dir_, file_ = splitdirfile(dirfile_)
  with open(dir_ + file_, 'rb') as f:
    data = pickle.load(f)
  return data