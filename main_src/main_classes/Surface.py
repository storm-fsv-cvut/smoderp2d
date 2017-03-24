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
import main_src.processes.surface              as surface
from   main_src.tools.tools                     import comp_type
isRill, subflow, stream, diffuse = comp_type()








class SurArrs :

  def __init__(self,sur_ret,inf_index, hcrit, a, b):

    self.state =       int(0)
    self.sur_ret =     sur_ret
    self.cur_sur_ret = float(0)
    self.h =           float(0)
    self.h_total =     float(0)
    self.h_total_pre =    float(0)
    self.V_runoff =     float(0)
    self.V_runoff_pre = float(0)
    self.V_rest =       float(0)
    self.V_rest_pre =   float(0)
    self.inflow_tm =    float(0)
    self.soil_type =    inf_index
    self.infiltration = float(0)
    self.h_crit =       hcrit
    self.a =            a
    self.b =            b
    self.h_rill =       float(0)
    self.h_rillPre =    float(0)
    self.V_runoff_rill= float(0)
    self.V_runoff_rill_pre= float(0)
    self.V_rill_rest =      float(0)
    self.V_rill_rest_pre =  float(0)
    self.rillWidth   =      float(0)
    self.V_to_rill   =      float(0)
    self.h_pre   =      float(0)


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
    self.shallowSurfaceKinematic = surface.shallowSurfaceKinematic
    self.rillCalculations        = rill.rillCalculations

    if (isRill) :
      prt.message("\tRill flow: \n\t\tON")
      self.runoff = self.__runoff
    else:
      prt.message("\tRill flow: \n\t\tOFF")
      self.runoff = self.__runoff_zero_compType

    super(Surface, self).__init__()



  ## Calculates the sheet and rill flow.
  #
  def __runoff(self,i,j,dt,efect_vrst,ratio) :

    arr = self.arr[i][j]

    self.update_state(i,j)
    self.compute_h_hrill(i,j)

    #if i == 8 : print "%.7f" % arr.h
    #if i == 8 : print "%.7f" % arr.h_rill 
    
    q_sheet = self.sheet_runoff(i,j,dt)

    if self.arr[i][j].h > 0.0 :
      v_sheet = q_sheet / arr.h
    else:
      v_sheet = 0.0



    if self.arr[i][j].state > 0 :
      q_rill, v_rill, ratio, rill_courant = self.rill_runoff(i,j,dt,efect_vrst,ratio)
    else:
      q_rill, v_rill, ratio, rill_courant = 0, 0, ratio, 0.0

    self.arr[i][j] = arr

    return q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant


  def __runoff_zero_compType(self,i,j,dt,efect_vrst,ratio) :

    arr = self.arr[i][j]

    q_sheet = self.sheet_runoff(i,j,dt)

    if arr.h > 0.0 :
      v_sheet = q_sheet / arr.h
    else:
      v_sheet = 0.0
    q_rill = 0
    v_rill = 0

    self.arr[i][j] = arr

    return q_sheet, v_sheet, q_rill, v_rill, ratio, 0.0


  def update_state(self,i,j):

    ht    = self.arr[i][j].h
    ht_1  = self.arr[i][j].h_total_pre
    hcrit = self.arr[i][j].h_crit
    state = self.arr[i][j].state
    test  = self.arr[i][j].state
    
    
    
    """
    if state == 0:
        if ht > hcrit:
            state = 1
    if state == 1:
        if ht> ht_1:
            pass
        elif ht > 2*hcrit:
            pass

        else:
            state = 2
            #print "chocho", ht, hcrit, ht_1
    if state == 2:
        if (ht > 2*hcrit):
            state = 1

    """
    #if i==1 and j==1 : print self.arr[i][j].h_total_pre,  self.arr[i][j].h, 
    err = 0 #
    #err = 0.00001
    if ht>hcrit :

      if state == 0:
        #print i, j, ht, ht_1
        state = 1
        
      elif state == 1 :
        if ht>=(ht_1-err) :
          pass
####### test #########
        else :
          #if i==1 and j==1 : print '\t aa state 2'
          state = 2
####### test #########

      elif state == 2:
        if ht>=(ht_1-err)      :
          pass
          #state = 1
        else :
          pass
####### test #########
    else:
      if state==1 :
        state = 2

    self.arr[i][j].state = state
    #print state
####### test #########
   
####### test #########
    #with open('teststateprehoz.txt', 'a') as file:
      #file.write(str(i) + ' ' + str(j) + ' ' + str(ht) + ' ' + str(ht_1) + ' ' + str(ht-ht_1) + ' ' + str(hcrit) + ' ' + str(test) + ' ' +str(state) + '\n')
####### test #########

  def compute_h_hrill(self,i,j):

    arr = self.arr[i][j]

    state = arr.state
    #print state
    #if i==6 and j==3 : print state, 'h', self.h
    if state == 0 :
      arr.h_rill = 0
      arr.h_pre = arr.h
    elif state == 1 :

####### test #########
      arr.h_rill = arr.h - arr.h_crit
      arr.h      = arr.h_crit
      arr.h_pre = arr.h_crit
      #arr.h_rill = max(arr.h - arr.h_crit,0.0)
      #arr.h      = min(arr.h,arr.h_crit)
####### test #########

      arr.h_rillPre = arr.h_rill
      """
    elif state == 2 :


      arr.h_rill = arr.h/2
      arr.h = arr.h_rill
      arr.h_rillPre = arr.h_rill
      arr.h_pre = arr.h


    """
    elif state == 2 :
      #raw_input() 

      arr.h_rill = arr.h_rillPre

      if (arr.h_rill < arr.h) :
        arr.h      = arr.h - arr.h_rill
      else:
        arr.h_rill = max(arr.h,0)
        arr.h      = 0.0

    #if i==1 and j==1 :  print arr.h, arr.h_rill
  def sheet_runoff(self,i,j,dt):
    #jj h musi byt aktualni v self.h !!!!

    arr = self.arr[i][j]

    q_sheet = self.shallowSurfaceKinematic(arr)
    arr.V_runoff = dt * q_sheet * self.dx
    arr.V_rest = arr.h * self.pixel_area - arr.V_runoff

    #self.arr[i][j] = arr

    return q_sheet

  def rill_runoff(self,i,j,dt,efect_vrst,ratio):

    arr = self.arr[i][j]

    #print arr.h_rill, arr.rillWidth,self.pixel_area,efect_vrst,constants.RILL_RATIO,mat_n[i][j],mat_slope[i][j],dt,ratio
    #sys.exit()
    
    
    #if i==2 and j == 1 : 
      ##print
      ##print 'i', "%.2d" % i
      #ppp = True
    #else :
    ppp = False
    
    #ppp = False
    #print i,j
    #if i==1 and j==1 : print 'hrill ', arr.h_rill
    if arr.state == 1 :
      arr.rillWidth = 0
    arr.rillWidth, \
    V_to_rill, \
    arr.V_runoff_rill, \
    arr.V_rill_rest, \
    q_rill, \
    v_rill, \
    ratio, \
    rill_courant = self.rillCalculations(arr,
                                         self.pixel_area,
                                         efect_vrst,
                                         constants.RILL_RATIO,
                                         mat_n[i][j],
                                         mat_slope[i][j],
                                         dt,
                                         ratio,ppp)


    #if i==8 : print  arr.h_rill * self.pixel_area, 
    #if i==8 : print "%.10f" %  arr.rillWidth, 
    #if ppp : print 'asdadsfadfadfad' "%.10f" %  arr.V_rill_rest,
    #if i==8 : print "%.10f" %  arr.V_runoff_rill
    #arr.h_rill = arr.V_rill_rest/self.pixel_area
    arr.V_to_rill = V_to_rill

    return q_rill, v_rill, ratio, rill_courant



  def bilance(self):
    pass




  def surface_retention(self,i,j,bil):

    reten = self.arr[i][j].sur_ret
    pre_reten = reten
    if reten < 0:
      tempBIL = bil + reten

      if tempBIL > 0:
        bil = tempBIL
        reten = 0
      else:
        reten = tempBIL
        bil = 0
    self.arr[i][j].sur_ret = reten
    self.arr[i][j].cur_sur_ret = reten-pre_reten

    return bil




  def return_str_vals(self,i,j,sep,dt):

    arr = self.arr[i][j]

    #Water_level_[m];Flow_[m3/s];V_runoff[m3];V_rest[m3];Infiltration[];surface_retention[l]
    line = str(arr.h) + sep + str(arr.V_runoff/dt) + sep + str(arr.V_runoff) + sep + str(arr.V_rest) + sep + str(arr.infiltration)+ sep + str(arr.cur_sur_ret)+ sep + str(arr.state) + sep + str(arr.inflow_tm)

    if self.rill_computing :
      #';Rill_size;Rill_flow;Rill_V_runoff;Rill_V_rest'
      line += sep + str(arr.h_rill) + sep + str(arr.rillWidth) + sep + str(arr.V_runoff_rill/dt) + sep + str(arr.V_runoff_rill) + sep + str(arr.V_rill_rest) + sep + str(arr.V_runoff/dt + arr.V_runoff_rill/dt) + sep + str(arr.V_runoff+arr.V_runoff_rill)
    #bil_  = arr.inflow_tm - arr.V_runoff - arr.V_runoff_rill - arr.cur_sur_ret*self.pixel_area - arr.V_rest + arr.V_rest_pre - arr.infiltration*self.pixel_area - arr.V_rill_rest + arr.V_rill_rest_pre
    bil_  = arr.inflow_tm - (arr.V_runoff + arr.V_runoff_rill + arr.infiltration*self.pixel_area) - (arr.cur_sur_ret*self.pixel_area + arr.V_rest + arr.V_rill_rest) + (arr.V_rest_pre + arr.V_rill_rest_pre)
    #bil_  = arr.inflow_tm - (arr.V_runoff + arr.infiltration*self.pixel_area) - (arr.cur_sur_ret*self.pixel_area + arr.V_rest) + (arr.V_rest_pre)
    return line, bil_




  def oscilace (self, i,j, pixel_area):
    arr = self.arr[i][j]
    oscilaceT =  False
    # last_step me plet, protoze last_step je vlastne ten soucasny...
    pre_step = arr.h_pre*pixel_area - arr.V_runoff_pre
    current_step = arr.h*pixel_area - arr.V_runoff
    #print arr.h_pre*pixel_area, arr.h*pixel_area
    #print arr.V_runoff_pre, arr.V_runoff
    #print pre_step, current_step
    if (pre_step - current_step) < 0:
        #print arr.h * pixel_area
        #print pre_step, current_step
        #print arr.V_runoff_pre, arr.V_runoff,
        oscilaceT = True
    return oscilaceT
