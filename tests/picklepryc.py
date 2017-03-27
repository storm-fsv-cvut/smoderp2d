#!/usr/bin/python

import numpy as np
import os
strr = 'adfadfadfa'
d = np.zeros([13,10])
ww = 0
for i in range(13):
  for j in range(10):
    d[i][j] = ww
    ww += 1
k = 123.1345
ll = [[],[],111324,112341,[22324,2233,2234],33344, [], [],[],[],4444999,[5552334,5553], 666,[],[],[1324134]]
#lll = [[1,1,1,1,1],[1231231],[231,312],[312],[]]
iii = int(1)
#dataList = [strr,d,k,ll,lll]
dataList = [iii,strr,k,ll,d]

#dataList = [k,ll]


  
  
  
  
  
  
  
class SaveItems :






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
    for item1 in b:
      line = ''
      for item2 in item1:
        line += str(item2) + ' ' 
      line = line[:-1]
      self.f.writelines(line + '\n') 




  def saveint(self,f) :
    self.f.writelines(str(f) + '\n') 


  def savefloat(self,f) :
    self.f.writelines(str(f) + '\n') 



  def savestr(self,s) :
    self.f.writelines(s + '\n') 
  
  def saveunicode(self,uni) :
    self.f.writelines(s + '\n') 


  def savenumpy(self,npa) :
    np.savetxt(self.f,npa)

class LoadItems :



  
  def loadlist(self):
    n = self.lines[1].replace('\n','').split(' ')
    n = int(n[0])
    line = []
    for i in self.lines[2:] :
      line.append(i.replace('\n','').split(' '))
      
    N = len(line)
    a = 0
    i = 0
    list_ = []
    
    wrk = []
    while i < (n-1) :
      if int(line[i][0]) > a :
        list_.append([])
        a+=1
        
      else:
        if int(line[i][0]) == a :
          wrk.append(int(line[i][1]))
        if i == (N-1) : break
        if int(line[i+1][0]) > a :
          list_.append(wrk)
          wrk = []
          a += 1
          
        i += 1
    
    if (n-1) == int(line[i][0]) :
      if int(line[N-1][0]) == int(line[N-2][0]) :
        list_.append(wrk)
      if int(line[N-1][0]) > int(line[N-2][0]) :
        list_.append([int(line[N-1][1])])
    else :
      while (N) >= i :
        list_.append([])
        i+=1
    return list_
  
  
  
  def loadint(self) :
    n = self.lines[1].replace('\n','').split(' ')
    return int(n[0])


  
  def loadfloat(self) :
    n = self.lines[1].replace('\n','').split(' ')
    return float(n[0])


  
  def loadstr(self) :
    n = self.lines[1].replace('\n','').split(' ')
    return n[0]

  def loadunicode(self) :
    n = self.lines[1].replace('\n','').split(' ')
    return n[0]
  
  
  def loadnpy(self) :
    
    n = len(self.lines[1:])
    m = len(self.lines[1].split(' '))
    arr = np.zeros([n,m],float)
    
    for i, line in  enumerate(self.lines[1:]) :
      for j, el in enumerate(line.split(' ')) :
        arr[i][j]= float(el)
    return arr



class SaveLoad(SaveItems,LoadItems):
  
  
  
  def save(self,data, dir_):
    if not os.path.exists(dir_):
      os.makedirs(dir_)
    for id_,it in enumerate(data):
      print id_
      with open(dir_+ os.sep + str(id_), 'w') as self.f:
        self.f.writelines(str(type(it))+'\n')
        self.save_item(it)

  
  
  def load(self,dir_):
    fs = sorted(os.listdir(dir_))
    listOut = []
    for fi in fs:
      with open(dir_+ os.sep + fi, 'r') as f:
        self.lines = f.readlines()
      listOut.append(self.load_item())
      
    return listOut



  def save_item(self,it):
    if isinstance(it,list) :
      self.savelist(it)
    if isinstance(it,float) :
      self.savefloat(it)
    if isinstance(it,str) :
      self.savestr(it)
    if isinstance(it,np.ndarray) :
      self.savenumpy(it)
    if isinstance(it,unicode) :
      self.saveunicode(it)
    if isinstance(it,int) :
      self.saveint(it)

  def load_item(self):
    if self.lines[0].replace('\n','') == str(type(list())) :
      return self.loadlist()
    if self.lines[0].replace('\n','') == str(type(float())) :
      return self.loadfloat()
    if self.lines[0].replace('\n','') == str(type(str())) :
      return self.loadstr()
    if self.lines[0].replace('\n','') == str(type(np.ones([2]))) :
      return self.loadnpy()
    if self.lines[0].replace('\n','') == str(type(unicode)) :
      return self.loadunicode()
    if self.lines[0].replace('\n','') == str(type(int())) :
      return self.loadint()






 
 
 
 
 
 
 










  
  
sl = SaveLoad()

sl.save(dataList,'./save/')
print dataList

del dataList

dataList = sl.load('./save/')



print dataList
