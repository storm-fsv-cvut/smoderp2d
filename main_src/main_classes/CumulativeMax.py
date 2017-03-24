## @package main_src.main_classes.CumulativeMax
#  
#  package contains classes save the cumulative or maximum
#  values of the results in each time step. 
#  
#  



# globals import 
import numpy as np



# smoderp import 
from   main_src.main_classes.General import *
from   main_src.tools.tools          import comp_type
import main_src.io_functions.prt         as prt



isRill, subflow, stream, diffuse = comp_type()






## Max and cumulative values of the subsurface flow 
#
#  Stores arrays of max or cumulative values of important variables of
#  the subsurface flow \n
#  
#  The class is inhered by the class Cumulative 
#  if the subsurface computation is desired 
#  
#  
class CumulativeSubsurface(object):
  
  
  ## constructor
  # 
  def __init__(self):


    prt.message('\tSubsurface')
    super(CumulativeSubsurface, self).__init__()


    
    self.arrs[14] = 'exfiltration'
    self.arrs[15] = 'percolation'
    self.arrs[16] = 'h_sub'
    self.arrs[17] = 'q_sub'
    self.arrs[18] = 'V_sub'



    self.names[14] = 'CumExfiltrL3'
    self.names[15] = 'CumPercolL3'
    self.names[16] = 'MaxWaterSubL'
    self.names[17] = 'MaxQSubL3t_1'
    self.names[18] = 'CumVOutSubL3'



    r = self.r
    c = self.c

    self.n += 5
    
    ## cumulative exfiltration volume [m3]
    self.exfiltration      =  np.zeros([r,c],float)
    ## cumulative percolation volume [m3]
    self.percolation      =  np.zeros([r,c],float)
    ## maximum water level in rills [m]
    # 
    #  the height is related to the total cell area not the rill ares 
    #
    self.h_sub      =  np.zeros([r,c],float)
    ## maximum discharge from rills [m3s-1]
    self.q_sub      =  np.zeros([r,c],float)
    ## cumulative outflow volume in rills [m3]
    self.V_sub      =  np.zeros([r,c],float)

  
  
  ## Method is used after each time step to save the desired variables.
  #  
  #  Method is called in main_src.runoff
  #  
  def update_cumulative_sur(self,i,j,sub,q_subsur):



    self.exfiltration[i][j] += sub.exfiltration*self.pixel_area
    self.percolation[i][j] += sub.percolation*self.pixel_area
    self.V_sub[i][j] += sub.V_runoff

    if sub.h > self.h_sub[i][j]:
      self.h_sub[i][j] = sub.h
    if q_subsur > self.q_sub[i][j]:
      self.q_sub[i][j] = q_subsur
 


## Empty (pass) Class
# 
# Class is inherited by the class Cumulative if the subsurface flow is not desired.
# 
class CumulativeSubsurfacePass(object):
  
  ## Method is used after each time step.
  #  
  #  Method is called in main_src.runoff
  #  
  def update_cumulative_sur(self,i,j,sub,q_subsur):
    pass











## Max and Cumulative values
#
#  Stores array of max or cumulative values at of important variables from
#  the surface and rill flow 
#  
#  
class Cumulative(CumulativeSubsurface if subflow == True else CumulativeSubsurfacePass, Globals,Size):




  ## the constructor
  #  
  #
  def __init__(self):
    
    prt.message('Save cumulative and maximum values from:')
    prt.message('\tSurface')
    
    
    ## Dictionary stores the python arrays identification. 
    #  
    #  self.arr is used in the main_src.io_functions.post_proc
    #  
    self.arrs = {1  : 'infiltration',
            2  : 'precipitation',
            3  : 'h_sur',
            4  : 'q_sur',
            5  : 'V_sur',
            6  : 'v_sur',
            7  : 'shear_sur',
            8  : 'h_rill',
            9  : 'q_rill',
            10 : 'V_rill',
            11 : 'b_rill',
            12 : 'inflow_sur',
            13 : 'sur_ret'
            }

            #12 : 'v_rill',


    ## Dictionary stores the the arrays name used in the output rasters. 
    #  
    #  self.names is used in the main_src.io_functions.post_proc
    #  
    self.names = {1  : 'CumInfiltL',
            2  : 'CumRainL',
            3  : 'MaxWateL',
            4  : 'MaxQL3t_1',
            5  : 'CumVOutL3',
            6  : 'MaxVelovity',
            7  : 'ShearStress',
            8  : 'MaxWaterRillL',
            9  : 'MaxQRillL3t_1',
            10 : 'CumVOutRillL3',
            11 : 'AreaRill',
            12 : 'CumVInL3',
            13 : 'SurRet'
            }
            #12 : 'MaxVeloRill',



    if (Globals.r == None or Globals.r == None):
      sys.exit("Global variables are not assigned")

    r = self.r
    c = self.c
    
    
    ## array count stored in the class
    self.n = 13
    ## cumulative infiltrated volume [m3]
    self.infiltration  =  np.zeros([r,c],float)
    ## cumulative precipitation volume [m3]
    self.precipitation =  np.zeros([r,c],float)
    ## maximum surface water level [m]
    self.h_sur  =  np.zeros([r,c],float)
    ## maximum surface discharge [m3s-1]
    self.q_sur  =  np.zeros([r,c],float)
    ## cumulative surface runoff volume [m3]
    self.V_sur  =  np.zeros([r,c],float)
    ## maximum surface velocity [ms-1]
    self.v_sur  =  np.zeros([r,c],float)
    ## maximum surface shear stress [Pa]
    self.shear_sur  =  np.zeros([r,c],float)
    ## cumulative surface inflow volume [m3]
    self.inflow_sur  =  np.zeros([r,c],float)
    ## maximum water level in rills [m]
    self.h_rill =  np.zeros([r,c],float)
    ## maximum discharge in rills [m3s-1]
    self.q_rill =  np.zeros([r,c],float)
    ## cumulative runoff volume in rills [m3]
    self.V_rill =  np.zeros([r,c],float)
    ## maximum rill width [m]
    self.b_rill =  np.zeros([r,c],float)
    ## maximum velocity in rills [ms-1]
    self.v_rill =  np.zeros([r,c],float)
    ## maximum surface retention [m]
    self.sur_ret=  np.zeros([r,c],float)

    
    super(Cumulative, self).__init__()


  
  
  ## Method is used after each time step to save the desired variables.
  #  
  #  Method is called in main_src.runoff
  #  
  def update_cumulative(self,i,j,surface,subsurface,rain,delta_t):


    self.infiltration[i][j]  += surface.infiltration*self.pixel_area
    self.precipitation[i][j] += rain*self.pixel_area
    self.V_sur[i][j]         += surface.V_runoff
    self.inflow_sur[i][j]    += surface.inflow_tm
    self.sur_ret[i][j]       += surface.cur_sur_ret*self.pixel_area

    q_sheet = surface.V_runoff/delta_t
    q_rill  = surface.V_runoff_rill/delta_t

    if surface.state == 0:
      if surface.h > self.h_sur[i][j]:
        self.h_sur[i][j] = surface.h
        self.q_sur[i][j] = q_sheet

    elif (surface.state == 1) or (surface.state == 2):

      self.V_rill[i][j] += surface.V_runoff_rill
      if surface.h > self.h_sur[i][j] :
        self.h_sur[i][j] = surface.h
        self.q_sur[i][j] = q_sheet

      elif surface.h_rill > self.h_rill[i][j]:
        self.h_rill[i][j]  = surface.h_rill
        self.b_rill[i][j]  = surface.b
        self.q_rill[i][j]  = q_rill


    self.update_cumulative_sur(i,j,subsurface.arr[i][j],subsurface.q_subsurface)








