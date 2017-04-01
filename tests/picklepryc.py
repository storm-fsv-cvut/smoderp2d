#!/usr/bin/python

# list blbne 
# chce ho rozlisit na int a float
# true false blbne 




import pickle
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
#ll = [[],[],111324,112341,[22324,2233,2234],33344, [], [],[],[],4444999,[5552334,5553], 666,[],[],[1324134]]
#lll = [[1,1,1,1,1],[1231231],[231,312],[312],[]]
#iii = int(1)
#dataList = [strr,d,k,ll,lll]
#dataList = [iii,strr,k,ll,d]

#dataList = [k,ll]
f = open('dp_hodne_bodu_tok.save','r')
dataList = pickle.load(f)
  
#l1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

#l2 = [[0, 1, 2, 3, 4, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 5], [0, 1, 2, 3, 4, 5]]

#l3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

#l4 = [[], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [] ]

#dataList = [l1,l2,l3,l4]
#for item in dataList:
  #print item

  
  
  
class SaveItems :






  def savelist(self,l):
    a = 0
    b = []
    self.f.writelines(str(len(l))+'\n')
    for i in range(len(l)):
      if l[i] == [] :
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
        line += str(item2) + ';' 
      line = line[:-1]
      self.f.writelines(line + '\n') 




  def saveint(self,f) :
    self.f.writelines(str(f) + '\n') 


  def savefloat(self,f) :
    self.f.writelines(str(f) + '\n') 



  def savestr(self,s) :
    self.f.writelines(s + '\n') 
  
  def saveunicode(self,uni) :
    self.f.writelines(uni + '\n') 


  def savenumpy(self,npa) :
    type_ = str(type(npa[0][0]))
    self.f.writelines (type_ + '\n')
    if 'int' in type_ :
      np.savetxt(self.f,npa,fmt = '%15d',delimiter=';')
    if 'float' in type_ :
      np.savetxt(self.f,npa,fmt = '%15.10e',delimiter=';')
      

class LoadItems :



  
  def loadlist(self,int_):
    
    if int_ : 
      self.el = self.__int
    else :
      self.el = self.__float
      
      
    nLinesList = self.lines[1].replace('\n','').split(';')
    nLinesList = int(nLinesList[0])
    
    line = []
    
    for i in self.lines[2:] :
      line.append(i.replace('\n','').split(';'))
      
    nRec = len(line)
    
    iLine = 0
    iRec = 0
    
    list_ = []
    wrk = []
    
    
    
    
    
    while iRec < (nRec-1) :
      if int(line[iRec][0]) > iLine :
        list_.append([])
        iLine+=1
        
      else:
        if int(line[iRec][0]) == iLine :
          wrk.append(self.el(line[iRec][1]))
          
        if int(line[iRec+1][0]) > iLine :
          if len(wrk) == 1 :
            list_.append(wrk[0])
          else:
            list_.append(wrk)
          wrk = []
          iLine += 1
        iRec += 1
    
    
    if (int(line[iRec][0]) == nLinesList-1) :
      wrk.append(self.el(line[iRec][1]))
      if len(wrk) == 1 :
        list_.append(wrk[0])
      else:
        list_.append(wrk)
    
    if (int(line[iRec][0]) < nLinesList-1) :
      for i in range(nLinesList-int(line[iRec][0])-1) :
        list_.append([])

    print list_
    print 
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
    
    n = len(self.lines[2:])
    m = len(self.lines[2].split(';'))
    type_ = self.lines[1]
    arr = np.zeros([n,m],float)
    
    if 'int' in type_ : 
      self.npyel = self.__int
    if 'float' in type_ :
      self.npyel = self.__float
    
    for i, line in  enumerate(self.lines[2:]) :
      for j, el in enumerate(line.split(';')) :
        arr[i][j]= self.npyel(el)
        
    return arr

  def __float(self,el):
    return float(el)
  
  def __int(self,el):
    return int(el)
  
  
class SaveLoad(SaveItems,LoadItems):

  
  def save(self,data, dir_):
    self.countList = 1
    if not os.path.exists(dir_):
      os.makedirs(dir_)
    for id_,it in enumerate(data):
      #print "%02d" % (id_)
      with open(dir_+ os.sep + "%02d" % (id_), 'w') as self.f:
        self.f.writelines(str(type(it))+'\n')
        self.save_item(it)

  
  
  def load(self,dir_):
    self.countList = 1
    fs = sorted(os.listdir(dir_))
    listOut = []
    for fi in fs:
      #print fi
      with open(dir_+ os.sep + fi, 'r') as f:
        self.lines = f.readlines()
      listOut.append(self.load_item())
      
    return listOut



  def save_item(self,it):
    if isinstance(it,list) :
      if self.countList in [1,2,3,4,5,8] : 
        print 'int'
      else:
        print 'float'
      print it
      print 
      self.savelist(it)
      self.countList += 1
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
      print self.countList, 
      if self.countList in [1,2,3,4,5,8] : 
        print 'int'
        self.countList += 1
        return self.loadlist(int_=True)
      
      else:
        print 'float'
        self.countList += 1
        return self.loadlist(int_=False)
      
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
#print dataList

del dataList
print '\n\n\n\n\n\n\n'#\n\n\n\n\n\n\n\n\n\n\n'
#print 'asdfasdfasdfasdfasdfadsfasdfasdfasdf'
#print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'

dataList = sl.load('./save/')


#for item in dataList :
  #print item

#print dataList
