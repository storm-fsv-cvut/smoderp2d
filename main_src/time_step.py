## @package main_src.time_step methods to performe
#  time step, and to store intermeriate variables



import main_src.processes.rainfall        as rain_f
import main_src.processes.infiltration    as infilt
from   main_src.tools.tools               import comp_type
import main_src.io_functions.prt          as prt
import copy
import numpy as np



from main_src.main_classes.Surface     import runoff
from main_src.main_classes.Surface     import surface_retention

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.000




## Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:

  #def __init__(self):
    #pass
    #self.r = G.r
    #self.c = G.c
    #self.rr = G.rr
    #self.rc = G.rc

    #self.V_rest_tmp        = np.zeros([self.r,self.c],float)
    #self.state_tmp         = np.zeros([self.r,self.c],float)
    #self.h_total_pre_tmp   = np.zeros([self.r,self.c],float)
    #self.sur_ret_tmp       = np.zeros([self.r,self.c],float)

    #isRill  = comp_type("rill")
    #subflow = comp_type("subflow")
    #stream  = comp_type("stream")

    #if isRill and not(subflow)  :
      #self.V_rill_rest_tmp   = np.zeros([self.r,self.c],float)
      ##self.V_rill_runoff_tmp = np.zeros([self.r,self.c],float)
      #self.rillWidth_tmp     = np.zeros([self.r,self.c],float)
      #self.save = self.__saveSurRill
      #self.undo = self.__undoSurRill

    #elif not(isRill) and subflow :
      #self.V_subf_rest_tmp   = np.zeros([self.r,self.c],float)
      #self.save = self.__saveSurSub
      #self.undo = self.__undoSurSub


    #elif isRill and subflow :
      #self.V_rill_rest_tmp   = np.zeros([self.r,self.c],float)
      #self.rillWidth_tmp     = np.zeros([self.r,self.c],float)
      #self.V_subf_rest_tmp   = np.zeros([self.r,self.c],float)
      #self.save = self.__saveSurSubRill
      #self.undo = self.__undoSurSubRill

    #else:
      #self.save = self.__saveSur
      #self.undo = self.__undoSur




  #def __saveSur(self,surArr, subArr):

    #for i in self.rr:
      #for j in self.rc[i]:
        #self.V_rest_tmp[i][j]     = surArr[i][j].V_rest
        ##self.V_runoff_tmp[i][j]   = surArr[i][j].V_runoff
        #self.state_tmp[i][j]      = surArr[i][j].state
        #self.h_total_pre_tmp[i][j]= surArr[i][j].h_total_pre
        #self.sur_ret_tmp[i][j]    = surArr[i][j].sur_ret


  #def __undoSur(self,surArr, subArr):
 
    #for i in self.rr:
      #for j in self.rc[i]:
        #surArr[i][j].V_rest        = self.V_rest_tmp[i][j]
        ##surArr[i][j].V_runoff      = self.V_runoff_tmp[i][j]
        #surArr[i][j].state         = self.state_tmp[i][j]
        #surArr[i][j].h_total_pre   = self.h_total_pre_tmp[i][j]
        #surArr[i][j].sur_ret       = self.sur_ret_tmp[i][j]


  #def __saveSurRill(self,surArr, subArr):

    #self.__saveSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #self.V_rill_rest_tmp[i][j] = surArr[i][j].V_rill_rest
        #self.rillWidth_tmp[i][j]   = surArr[i][j].rillWidth
        ##self.V_rill_runoff_tmp[i][j]   = surArr[i][j].V_runoff_rill

  #def __undoSurRill(self,surArr, subArr):
    #self.__undoSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #surArr[i][j].V_rill_rest = self.V_rill_rest_tmp[i][j]
        #surArr[i][j].rillWidth   = self.rillWidth_tmp[i][j]
        ##surArr[i][j].V_runoff_rill=self.V_rill_runoff_tmp[i][j]


  #def __saveSurSub(self,surArr, subArr):
    #self.__saveSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #self.V_subf_rest_tmp[i][j] = subArr[i][j].V_rest


  #def __undoSurSub(self,surArr, subArr):
    #self.__undoSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #subArr[i][j].V_rest = self.V_subf_rest_tmp[i][j]



  #def __saveSurSubRill(self,surArr, subArr):
    #self.__saveSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #self.V_rill_rest_tmp[i][j] = surArr[i][j].V_rill_rest
        #self.rillWidth_tmp[i][j]   = surArr[i][j].rillWidth
        #self.V_subf_rest_tmp[i][j] = subArr[i][j].V_rest

  #def __undoSurSubRill(self,surArr, subArr):
    #self.__undoSur(surArr, subArr)
    #for i in self.rr:
      #for j in self.rc[i]:
        #surArr[i][j].V_rill_rest = self.V_rill_rest_tmp[i][j]
        #surArr[i][j].rillWidth   = self.rillWidth_tmp[i][j]
        #subArr[i][j].V_rest = self.V_subf_rest_tmp[i][j]


  
  
  def do_flow(self,surface, subsurface,delta_t,G, mat_efect_vrst, ratio, courant,itera, total_time, tz, sr) :
    
    """
    global infilt_capa
    global max_infilt_capa
    global infilt_time
    """
    rrows = G.rr
    rcols = G.rc
    pixel_area = G.pixel_area
    
    
    rainfall, tz = rain_f.timestepRainfall(itera,total_time,delta_t,tz,sr)
    """
    infilt_capa += rainfall
    if (infilt_capa < max_infilt_capa) :
      infilt_time += delta_t_pre
      NS = 0.0
      rainfall = 0.0
      return NS, surface, subsurface,  tz, sum_interception, ratio, rainfall, 0.0, 0.0, 0.0
    """
    
    
    for i in rrows:
      for j in rcols[i]:
        
        h_total_pre   = surface.arr[i][j].h_total_pre
        
        h_total_pre -= surface_retention(surface.arr[i][j])
        
        surface_state = surface.arr[i][j].state
        
        #
        if surface_state >= 1000:
          # toto je pripraveno pro odtok v ryhach
          q_sheet = 0.0
          q_rill  = 0.0
          v_sheet = 0.0
          rill_courant = 0.0
          surface.arr[i][j].V_runoff = 0.0
          surface.arr[i][j].V_rest   = 0.0

          h_sub = subsurface.runoff_stream_cell(i,j)

          inflowToReach =  h_sub*pixel_area + h_total_pre*pixel_area
          surface.reach_inflows(id_=int(surface_state-1000),inflows=inflowToReach)

        else:

          q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant = runoff(i,j,surface.arr[i][j],delta_t, mat_efect_vrst[i][j], ratio)
          subsurface.runoff(i,j,delta_t, mat_efect_vrst[i][j])

        q_surface = q_sheet+q_rill

        v = v_sheet
        co='sheet'
        #print surface.arr[i][j].h_sheet, surface.arr[i][j].h_total_pre, v, q_sheet, surface.arr[i][j].V_runoff
        courant.CFL(i,j,surface.arr[i][j].h_total_pre,v,delta_t,mat_efect_vrst[i][j],co, rill_courant)
       
    return ratio, v_sheet, v_rill, rainfall, tz
    
  
  
  
  
  
  
  def do_next_h(self,surface, subsurface, rain_arr, cumulative, hydrographs, rainfall, courant, G, total_time, delta_t, combinatIndex, NoDataValue, sum_interception, mat_efect_vrst, ratio, iter_):



    rrows = G.rr
    rcols = G.rc
    pixel_area = G.pixel_area
    #ratio_tmpp = ratio




    for iii in combinatIndex:
        index = iii[0]
        k = iii[1]
        s =  iii[2]
        #jj * 100.0 !!! smazat
        iii[3] = infilt.phlilip(k, s, delta_t, total_time-infilt_time, NoDataValue)
        #print total_time-infilt_time, iii[3]*1000, k, s

    infilt.set_combinatIndex(combinatIndex)



    #
    #nulovani na zacatku kazdeho kola
    #
    surface.reset_inflows()
    surface.new_inflows()

    subsurface.fill_slope()
    subsurface.new_inflows()

    for i in rrows:
      for j in rcols[i]:
        
        #print i,j, surface.arr[i][j].h_total_pre, surface.arr[i][j].V_runoff
        #
        # current cell precipitation
        #
        #print rain_arr.arr[i][j], rainfall, sum_interception
        NS, sum_interception, rain_arr.arr[i][j].veg_true = rain_f.current_rain(rain_arr.arr[i][j], rainfall, sum_interception)
        surface.arr[i][j].cur_rain = NS
        #
        # Inflows from surroundings cells
        #
        surface.arr[i][j].inflow_tm = surface.cell_runoff(i,j)
        
        #
        # Surface BILANCE
        #
        surBIL =  surface.arr[i][j].h_total_pre + NS + surface.arr[i][j].inflow_tm/pixel_area - (surface.arr[i][j].V_runoff/pixel_area + surface.arr[i][j].V_runoff_rill/pixel_area)

        #
        # infiltration
        #
        if subsurface.get_exfiltration(i,j) > 0 :
          surface.arr[i][j].infiltration = 0.0
          infiltration =  0.0
          #print 'NS', NS
        else :
          surBIL, infiltration = infilt.philip_infiltration(surface.arr[i][j].soil_type,surBIL)
          surface.arr[i][j].infiltration = infiltration

        # surface retention
        surBIL +=  subsurface.get_exfiltration(i,j)
        #print surBIL
        
        surface.arr[i][j].h_total_new = surBIL
        
        #print surface.arr[i][j].h_sheet, surface.arr[i][j].h_total_pre, infiltration, NS,  surface.arr[i][j].inflow_tm/pixel_area
        surface_state   = surface.arr[i][j].state
        # subsurface inflow
        """
        inflow_sub = subsurface.cell_runoff(i,j,False)
        subsurface.bilance(i,j,infiltration,inflow_sub/pixel_area,delta_t)
        subsurface.fill_slope()
        """
        cumulative.update_cumulative(i,j,surface.arr[i][j], subsurface,delta_t)
        hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,NS)
        
    return NS, sum_interception
