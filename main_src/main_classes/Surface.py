import numpy as np
import math
import sys
import os
#import psutil

from   main_src.tools.resolve_partial_computing import *
from main_src.main_classes.General              import *
from main_src.main_classes.KinematicDiffuse     import *
from main_src.main_classes.Stream               import *


import main_src.processes.rill                 as rill
import main_src.io_functions.prt               as prt
import main_src.processes.surface              as surfacefce
from   main_src.tools.tools                     import comp_type
isRill, subflow, stream, diffuse = comp_type()








class SurArrs :

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
    #self.h_rillPre =    float(0)
    self.V_runoff_rill= float(0)
    #self.V_runoff_rill_pre= float(0)
    self.V_rill_rest =      float(0)
    #self.V_rill_rest_pre =  float(0)
    self.rillWidth   =      float(0)
    self.V_to_rill   =      float(0)


## Documentation for a class Surface.
#
#  Class Surface contains data and methods
#  to calculate the surface and rill runoff
#
class Surface(Stream if stream == True else StreamPass,Kinematic,Globals,Size):


  ## The constructor
  #  make all numpy arrays and establish the inflow procedure based on D8 or Multi Flow Direction Algorithm method
  def __init__(self,sur_ret,mat_inf_index,mat_hcrit,mat_aa,mat_b):

    prt.message("Surface:")

    self.n = 15
    self.arr = np.empty((self.r,self.c), dtype=object)

    for i in range(self.r):
      for j in range(self.c):
        #jj
        self.arr[i][j] = SurArrs(sur_ret,mat_inf_index[i][j],mat_hcrit[i][j],mat_aa[i][j],mat_b[i][j])
        #self.arr[i][j] = SurArrs(sur_ret,mat_inf_index[i][j],0.0025,mat_aa[i][j],mat_b[i][j])

    #raw_input()
    self.rill_computing          = isRill
    #self.shallowSurfaceKinematic = surface.shallowSurfaceKinematic
    #self.rillCalculations        = rill.rillCalculations


    super(Surface, self).__init__()


  def return_str_vals(self,i,j,sep,dt):

    arr = self.arr[i][j]

    #Water_level_[m];Flow_[m3/s];V_runoff[m3];V_rest[m3];Infiltration[];surface_retention[l]
    line = str(arr.h_sheet) + sep + str(arr.V_runoff/dt) + sep + str(arr.V_runoff) + sep + str(arr.V_rest) + sep + str(arr.infiltration)+ sep + str(arr.cur_sur_ret)+ sep + str(arr.state) + sep + str(arr.inflow_tm)

    if self.rill_computing :
      #';Rill_size;Rill_flow;Rill_V_runoff;Rill_V_rest'
      line += sep + str(arr.h_rill) + sep + str(arr.rillWidth) + sep + str(arr.V_runoff_rill/dt) + sep + str(arr.V_runoff_rill) + sep + str(arr.V_rill_rest) + sep + str(arr.V_runoff/dt + arr.V_runoff_rill/dt) + sep + str(arr.V_runoff+arr.V_runoff_rill)
    #bil_  = arr.inflow_tm - arr.V_runoff - arr.V_runoff_rill - arr.cur_sur_ret*self.pixel_area - arr.V_rest + arr.V_rest_pre - arr.infiltration*self.pixel_area - arr.V_rill_rest + arr.V_rill_rest_pre
    bil_  = arr.h_total_pre*self.pixel_area + arr.cur_rain*self.pixel_area + arr.inflow_tm - (arr.V_runoff + arr.V_runoff_rill + arr.infiltration*self.pixel_area) - (arr.cur_sur_ret*self.pixel_area) - arr.h_total_new*self.pixel_area #<< + arr.V_rest + arr.V_rill_rest) + (arr.V_rest_pre + arr.V_rill_rest_pre)
    #bil_  = arr.inflow_tm - (arr.V_runoff + arr.infiltration*self.pixel_area) - (arr.cur_sur_ret*self.pixel_area + arr.V_rest) + (arr.V_rest_pre)
    return line, bil_





## Calculates the sheet and rill flow.
#
def __runoff(i,j,sur,dt,efect_vrst,ratio) :
  
  h_tota_pre = sur.h_total_pre
  h_crit     = sur.h_crit
  state      = sur.state
  
  #sur.state               = update_state1(h_tota_pre,h_crit,state)
  sur.h_sheet, sur.h_rill = compute_h_hrill(h_tota_pre,h_crit,state)
  
  q_sheet = sheet_runoff(sur,dt)
  
  
  if sur.h_sheet > 0.0 :
    v_sheet = q_sheet / sur.h_sheet
  else:
    v_sheet = 0.0



  if sur.state > 0 :
    q_rill, v_rill, ratio, rill_courant = rill_runoff(i,j,sur,dt,efect_vrst,ratio)
  else:
    q_rill, v_rill, ratio, rill_courant = 0, 0, ratio, 0.0

  #print q_sheet
  return q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant







def __runoff_zero_compType(i,j,sur,dt,efect_vrst,ratio) :

  h_tota_pre = sur.h_total_pre
  h_crit     = sur.h_crit
  state      = sur.state
  
  #sur.state               = update_state1(h_tota_pre,h_crit,state)
  sur.h_sheet = sur.h_total_pre
  
  q_sheet = sheet_runoff(sur,dt)
  
  
  if sur.h_sheet > 0.0 :
    v_sheet = q_sheet / sur.h_sheet
  else:
    v_sheet = 0.0


  q_rill = 0
  v_rill = 0


  return q_sheet, v_sheet, q_rill, v_rill, ratio, 0.0


def update_state1(ht_1,hcrit,state):
  if ht_1>hcrit :
    if state == 0:
      return 1
  return state  


def compute_h_hrill(h_total_pre,h_crit,state):

  if state == 0 :
    h_sheet = h_total_pre
    h_rill  = 0
    return h_sheet, h_rill
  
  elif state == 1 :
    h_sheet   = h_crit
    h_rill    = h_total_pre - h_crit
    return h_sheet, h_rill
  
  elif state == 2 :
    h_sheet   = min(h_total_pre,h_crit)
    h_rill    = max(0,h_total_pre - h_crit)
    return h_sheet, h_rill
  

def sheet_runoff(sur,dt):


  q_sheet = surfacefce.shallowSurfaceKinematic(sur)
  sur.V_runoff = dt * q_sheet * Globals.dx
  sur.V_rest = sur.h_sheet * Globals.pixel_area - sur.V_runoff

  return q_sheet

def rill_runoff(i,j,sur,dt,efect_vrst,ratio):
  ppp = False
  

  if sur.state == 1 :
    sur.rillWidth = 0
    
  sur.rillWidth, \
  V_to_rill, \
  sur.V_runoff_rill, \
  sur.V_rill_rest, \
  q_rill, \
  v_rill, \
  ratio, \
  rill_courant = rill.rillCalculations(sur,
                                        pixel_area,
                                        efect_vrst,
                                        constants.RILL_RATIO,
                                        mat_n[i][j],
                                        mat_slope[i][j],
                                        dt,
                                        ratio,ppp)



  sur.V_to_rill = V_to_rill
  
  return q_rill, v_rill, ratio, rill_courant




def surface_retention(sur):

  reten = sur.sur_ret
  pre_reten = reten
  if reten < 0:
    tempBIL = sur.h_tota_pre + reten

    if tempBIL > 0:
      bil = tempBIL
      reten = 0
    else:
      reten = tempBIL
      bil = 0
      
  sur.sur_ret = reten
  sur.cur_sur_ret = reten-pre_reten

  return sur.cur_sur_ret









if (isRill) :
  prt.message("\tRill flow: \n\t\tON")
  runoff = __runoff
else:
  #raw_input()
  prt.message("\tRill flow: \n\t\tOFF")
  runoff = __runoff_zero_compType
