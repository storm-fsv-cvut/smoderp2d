import numpy as np

from   main_src.tools.resolve_partial_computing import *
from main_src.main_classes.General import *



class VegArrs:
  def __init__(self,veg_true,ppl,pi):
    self.veg_true = veg_true
    self.ppl      = ppl
    self.pi       = pi


## Documentation for a class.
#  More details.
#
class Vegetation(Globals,Size):


  ## The constructor.
  def __init__(self,mat_ppl,mat_pi):

    if (Globals.r == None or Globals.r == None):
      exit("Global variables are not assigned")

    self.n = 3
    self.arr = np.empty((self.r,self.c), dtype=object)

    for i in range(self.r):
      for j in range(self.c):
        self.arr[i][j] = VegArrs(0,mat_ppl[i][j],mat_pi[i][j])
        
        
        
        