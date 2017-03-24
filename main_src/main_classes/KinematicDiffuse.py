



from main_src.main_classes.General import *
from main_src.main_classes.Flow import *


import main_src.io_functions.prt          as prt
import main_src.flow_algorithm.flow_direction       as flow_direction






class Kinematic(Mfda if mfda==True else D8):

  def __init__(self):
    prt.message("\tKinematic approach")
    super(Kinematic, self).__init__()

  def new_inflows(self):
    pass

  def update_H(self):
    pass















class Diffuse(Mfda if mfda==True else D8, Globals):

  def __init__(self):
    prt.message("\tDiffuse approach")
    if (Globals.r == None or Globals.r == None):
      exit("Global variables are not assigned")
    r = self.r
    c = self.c

    self.H = np.zeros([r,c],float)

  def new_inflows(self):
    fd = flow_direction.flow_direction(self.H,self.rr,self.rc,self.br,self.bc,self.pixel_area)
    self.update_inflows(fd)


  def update_H(self):

    arr = self.arr

    for i in self.rr:
      for j in self.rc[i]:
        arr.H[i][j] = arr.h[i][j] + arr.z[i][j]

        
    for i in self.rr:
      for j in self.rc[i]:
        arr.slope = self.slope_(i,j)


