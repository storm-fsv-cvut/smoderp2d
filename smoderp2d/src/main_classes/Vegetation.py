

import numpy as np

from smoderp2d.src.main_classes.General import Size



class VegArrs:
  def __init__(self,veg_true,ppl,pi):
    self.veg_true = veg_true
    self.ppl      = ppl
    self.pi       = pi


## Documentation for a class.
#  More details.
#
class Vegetation(Size):


  ## The constructor.
  def __init__(self,r,c,mat_ppl,mat_pi):

    self.n = 3
    self.arr = np.empty((r,c), dtype=object)

    for i in range(r):
      for j in range(c):
        self.arr[i][j] = VegArrs(0,mat_ppl[i][j],mat_pi[i][j])
        
        
        
        