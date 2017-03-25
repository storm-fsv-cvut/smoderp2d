#!/usr/bin/python

import numpy as np
import os
strr = 'adfadfadfa'
d = np.ones([13,13])
k = 123.1345
ll = [1324,12341,1.1324,1324]
lll = [[1,1,1,1,1],[1231231],[231,312],[312],[]]

dataList = [strr,d,k,ll,lll]

class SaveLoad:
  
  
  
  def save(self,data, dir_):
    if not os.path.exists(dir_):
      os.makedirs(dir_)
    for id_,it in enumerate(data):
      #print id_, it, '\n'
      with open(dir_+ os.sep + str(id_), 'w') as self.f:
        # write type
        self.f.writelines(str(type(it))+'\n')
        self.save_item(it)

  
  
  def load(self,dir_):
    fs = os.listdir(dir_)
    for fi in fs:
      with open(dir_+ os.sep + fi, 'r') as f:
        self.lines = f.readlines()
      self.load_item()  

  def save_item(self,it):
    if isinstance(it,list) :
      self.savelist(it)
      


  def load_item(self):
    if self.lines[0].replace('\n','') == str(type(list())) :
      self.loadlist()      
      








  def savelist(self,l):
    a = 0
    b = []
    self.f.writelines(str(len(l))+'\n')
    for i in range(len(l)):
      if not l[i] :
        pass
      else:
        if isinstance(l[i],list) :
          for j in range(len(l[i])):
            b.append([a,l[i][j]])
        else :
          b.append([a,l[i]])
      a += 1
      #b.append(a)
    for item1 in b:
      line = ''
      for item2 in item1:
        line += str(item2) + ' ' 
      line = line[:-1]
      self.f.writelines(line + '\n') 
      #self.f.writelines( str([i, l[i]]).replace('[','').replace(']','').replace(',','')+'\n' )
 
  
  def loadlist(self):
    n = self.lines[1].replace('\n','').split(' ')
    a = 0
    list_ = []
    wrk = []
    print 
    for line in self.lines[2:] :
      l = line.replace('\n','').split(' ')
      m = int(l[0])
      if not l[1]:
        pass
      else:
        wrk.append(l[1])
      print m, a
      #if m > a :
        #while m > a :
          #list_.append([])
          #a += 1
      #if m == a :
        #wrk.append(l[1])
        
      if m > a :
        print '   zapis'    
        list_.append(wrk)
        wrk = []
        a+=1 
    print list_ 

sl = SaveLoad()

sl.save(dataList,'./save/')


del dataList

dataList = sl.load('./save/')
