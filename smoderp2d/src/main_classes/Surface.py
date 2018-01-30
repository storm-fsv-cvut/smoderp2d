## @package smoderp2d.src.main_classes.Surface
#
#  Package contains classes and methods to campute 
#  surface processes





import numpy as np
import math
import sys
import os
#import psutil

from smoderp2d.src.main_classes.General              import *
from smoderp2d.src.main_classes.KinematicDiffuse     import *
from smoderp2d.src.main_classes.Stream               import *


import smoderp2d.src.processes.rill                 as rill
import smoderp2d.src.constants                      as constants
import smoderp2d.src.io_functions.prt               as prt
import smoderp2d.src.processes.surface              as surfacefce
from   smoderp2d.src.tools.tools                     import comp_type
isRill, subflow, stream, diffuse = comp_type()








courantMax = 1.0



## Main surface class
# 
#  Class contains a set of surface perameters
class SurArrs :

  ## Constructor of Surface array
  #  
  #  assign values into surface parameters
  def __init__(self,sur_ret,inf_index, hcrit, a, b):

    self.state =       int(0)
    self.sur_ret =     sur_ret
    self.cur_sur_ret = float(0)
    self.cur_rain    = float(0)
    self.h_sheet =     float(0)
    self.h_total_new =    float(0)
    self.h_total_pre =    float(0)
    self.V_runoff =     float(0)
    #self.V_runoff_pre = float(0)
    self.V_rest =       float(0)
    #self.V_rest_pre =   float(0)
    self.inflow_tm =    float(0)
    self.soil_type =    inf_index
    self.infiltration = float(0)
    self.h_crit =       hcrit
    self.a =            a
    self.b =            b
    self.h_rill =       float(0)
    self.h_rillPre =    float(0)
    self.V_runoff_rill= float(0)
    #self.V_runoff_rill_pre= float(0)
    self.V_rill_rest =      float(0)
    #self.V_rill_rest_pre =  float(0)
    self.rillWidth   =      float(0)
    self.V_to_rill   =      float(0)
    self.h_last_state1 =    float(0)


## Documentation for a class Surface.
#
#  Class Surface contains data and methods
#  to calculate the surface and rill runoff
#
class Surface(Stream if stream == True else StreamPass,Kinematic,Globals,Size):


  ## The constructor
  #  make all numpy arrays and establish the inflow procedure based on D8 or Multi Flow Direction Algorithm method
  def __init__(self,r,c,mat_reten,mat_inf_index,mat_hcrit,mat_aa,mat_b):

    prt.message("Surface:")
    
    
    
    self.n = 15
    self.arr = np.empty((self.r,self.c), dtype=object)
    self.r = r
    self.c = c 
    
    for i in range(self.r):
      for j in range(self.c):
        #jj                           prevod na m y mm
        self.arr[i][j] = SurArrs(-mat_reten[i][j]/1000.,mat_inf_index[i][j],mat_hcrit[i][j],mat_aa[i][j],mat_b[i][j])
        #self.arr[i][j] = SurArrs(sur_ret,mat_inf_index[i][j],0.0025,mat_aa[i][j],mat_b[i][j])


    self.rill_computing          = isRill

    if (isRill) :
      prt.message("\tRill flow: \n\t\tON")
    else:
      #raw_input()
      prt.message("\tRill flow: \n\t\tOFF")


    super(Surface, self).__init__()




  
  def return_str_vals(self,i,j,sep,dt,extraOut):

    arr = self.arr[i][j]

    #Water_level_[m];Flow_[m3/s];V_runoff[m3];V_rest[m3];Infiltration[];surface_retention[l]
    
    
    if not(extraOut) :
      line = str(arr.h_total_new) + sep + str(arr.V_runoff/dt + arr.V_runoff_rill/dt) + sep + str(arr.V_runoff+arr.V_runoff_rill)
      bil_ = ''
    else :
      line = str(arr.h_sheet) + sep + str(arr.V_runoff/dt) + sep + str(arr.V_runoff) + sep + str(arr.V_rest) + sep + str(arr.infiltration)+ sep + str(arr.cur_sur_ret)+ sep + str(arr.state) + sep + str(arr.inflow_tm) + sep + str(arr.h_total_new)

      if self.rill_computing :

        line += sep + str(arr.h_rill) + sep + str(arr.rillWidth) + sep + str(arr.V_runoff_rill/dt) + sep + str(arr.V_runoff_rill) + sep + str(arr.V_rill_rest) + sep + str(arr.V_runoff/dt + arr.V_runoff_rill/dt) + sep + str(arr.V_runoff+arr.V_runoff_rill) + sep

      bil_  = arr.h_total_pre*self.pixel_area + arr.cur_rain*self.pixel_area + arr.inflow_tm - (arr.V_runoff + arr.V_runoff_rill + arr.infiltration*self.pixel_area) - (arr.cur_sur_ret*self.pixel_area) - arr.h_total_new*self.pixel_area #<< + arr.V_rest + arr.V_rill_rest) + (arr.V_rest_pre + arr.V_rill_rest_pre)

    return line, bil_





## Calculates the sheet and rill flow.
#
def __runoff(i,j,sur,dt,efect_vrst,ratio) :

  h_total_pre = sur.h_total_pre
  h_crit     = sur.h_crit
  state      = sur.state # da se tady podivat v jakym jsem casovym kroku a jak se a

  #sur.state               = update_state1(h_total_pre,h_crit,state)
  sur.h_sheet, sur.h_rill, sur.h_rillPre = compute_h_hrill(h_total_pre,h_crit,state,sur.rillWidth,sur.h_rillPre)
  


  q_sheet = sheet_runoff(sur,dt)


  if sur.h_sheet > 0.0 :
    v_sheet = q_sheet / sur.h_sheet
  else:
    v_sheet = 0.0



  if sur.state > 0 :
    q_rill, v_rill, ratio, rill_courant = rill_runoff(i,j,sur,dt,efect_vrst,ratio)
  else:
    q_rill, v_rill, ratio, rill_courant = 0, 0, ratio, 0.0

  #print 'sur.V_runoff', sur.V_runoff, sur.V_runoff_rill
  return q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant







def __runoff_zero_compType(i,j,sur,dt,efect_vrst,ratio) :

  h_total_pre = sur.h_total_pre
  h_crit     = sur.h_crit
  state      = sur.state

  #sur.state               = update_state1(h_total_pre,h_crit,state)
  sur.h_sheet = sur.h_total_pre

  q_sheet = sheet_runoff(sur,dt)


  if sur.h_sheet > 0.0 :
    v_sheet = q_sheet / sur.h_sheet
  else:
    v_sheet = 0.0


  q_rill = 0
  v_rill = 0


  return q_sheet, v_sheet, q_rill, v_rill, ratio, 0.0






def update_state1(ht_1,hcrit,state,rillWidth):
  if ht_1>hcrit :
    if state == 0:
      return 1
  return state







def compute_h_hrill(h_total_pre,h_crit,state,rillWidth,hRillPre):

  if state == 0 :
    h_sheet = h_total_pre
    h_rill  = 0
    return h_sheet, h_rill, 0

  elif state == 1 :
    h_sheet   = min(h_crit,              h_total_pre)
    h_rill    = max(h_total_pre - h_crit,0)
    hRillPre  = h_rill
    #print "%d, %.6e, %.6e" % (state, h_sheet, h_rill)
    return h_sheet, h_rill, hRillPre

  elif state == 2 :
    
    if (h_total_pre>hRillPre) :
      h_rill    = hRillPre
      h_sheet   = h_total_pre-hRillPre
    else :
      h_rill    = h_total_pre
      h_sheet   = 0
    
    return h_sheet, h_rill, hRillPre
















def sheet_runoff(sur,dt):


  q_sheet = surfacefce.shallowSurfaceKinematic(sur)
  sur.V_runoff = dt * q_sheet * Globals.dx
  sur.V_rest = sur.h_sheet * Globals.pixel_area - sur.V_runoff

  return q_sheet















def rill_runoff(i,j,sur,dt,efect_vrst,ratio):

  ppp = False

  V_to_rill = sur.h_rill*Globals.pixel_area
  h, b   = rill.update_hb(V_to_rill,constants.RILL_RATIO,efect_vrst,sur.rillWidth,ratio,ppp)
  R_rill = (h*b)/(b + 2*h)
  #print '\t', h,b, b, 2*h
  v_rill = math.pow(R_rill,(2.0/3.0)) * 1./Gl.mat_n[i][j] * math.pow(Gl.mat_slope[i][j]/100,0.5)
  #print "V_to_rill, R_rill", V_to_rill, R_rill
  #q_rill = v_rill * constants.RILL_RATIO * b * b # [m3/s]
  
  q_rill = v_rill * h * b
  
  
  V      = q_rill*dt
  
  # puvodni podle rychlosti
  courant = (v_rill*dt)/efect_vrst
  
  # celerita 
  #courant = (1 + s*b/(3*(b+2*h))) * q_rill/(b*h)
  
  
  
  sur.V_to_rill = V_to_rill
  sur.rillWidth = b
  if (courant <= courantMax) :

    if V>(V_to_rill):
      sur.V_rill_rest   = 0
      sur.V_runoff_rill = V_to_rill

    else:
      sur.V_rill_rest   = V_to_rill - V
      sur.V_runoff_rill = V

  else:
    return q_rill, v_rill, ratio, courant

  return q_rill, v_rill, ratio, courant









def surface_retention(bil,sur):

  reten = sur.sur_ret
  pre_reten = reten
  
  if reten < 0:
    tempBIL = bil + reten

    if tempBIL > 0:
      bil = tempBIL
      reten = 0
    else:
      reten = tempBIL
      bil = 0

  sur.sur_ret = reten
  sur.cur_sur_ret = reten-pre_reten
  return bil










if (isRill) :
  runoff = __runoff
else:
  runoff = __runoff_zero_compType

