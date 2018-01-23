## @package smoderp2d.src.time_step methods to performe
#  time step, and to store intermeriate variables



import smoderp2d.src.processes.rainfall        as rain_f
import smoderp2d.src.processes.infiltration    as infilt
from   smoderp2d.src.tools.tools               import comp_type
import smoderp2d.src.io_functions.prt          as prt
import copy
import numpy as np



from smoderp2d.src.main_classes.Surface     import runoff
from smoderp2d.src.main_classes.Surface     import surface_retention

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.003 #[m]


  

## Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:



  def do_flow(self,rr,rc,surface, subsurface,delta_t, mat_efect_vrst, ratio, courant,itera, total_time, tz, sr) :




    
    rainfall, tz = rain_f.timestepRainfall(itera,total_time,delta_t,tz,sr)


    for i in rr:
      for j in rc[i]:

        h_total_pre   = surface.arr[i][j].h_total_pre



        surface_state = surface.arr[i][j].state

        if surface_state >= 1000:
          q_sheet = 0.0
          v_sheet = 0.0
          q_rill = 0.0
          v_rill = 0.0
          rill_courant = 0.0
        else :
          q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant = runoff(i,j,surface.arr[i][j],delta_t, mat_efect_vrst[i][j], ratio)
          subsurface.runoff(i,j,delta_t, mat_efect_vrst[i][j])

        q_surface = q_sheet+q_rill
        #print v_sheet,v_rill
        v = max(v_sheet,v_rill)
        co='sheet'
        courant.CFL(i,j,surface.arr[i][j].h_total_pre,v,delta_t,mat_efect_vrst[i][j],co, rill_courant)
        rill_courant = 0.
        
        #w1 = surface.arr[i][j].V_runoff_rill
        #w2 = surface.arr[i][j].V_rill_rest
        #print surface.arr[i][j].h_total_pre
        #if (w1 > 0 and w2 == 0) :
          #print 'asdf', w1, w2

    return ratio, v_sheet, v_rill, rainfall, tz







  def do_next_h(self,rr,rc,pixel_area, surface, subsurface, rain_arr, cumulative, hydrographs, rainfall, courant, total_time, delta_t, combinatIndex, NoDataValue, sum_interception, mat_efect_vrst, ratio, iter_):

    global infilt_capa
    global max_infilt_capa
    global infilt_time


    #ratio_tmpp = ratio

    infilt_capa += rainfall
    if (infilt_capa < max_infilt_capa) :
      infilt_time += delta_t
      NS = 0.0
      rainfall = 0.0
      for i in rr:
        for j in rc[i]:
          hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,NS)
      return NS, sum_interception

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

    #print 'bbilll'
    for i in rr:
      for j in rc[i]:

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
        # surface retention
        #
        surBIL = surface_retention(surBIL,surface.arr[i][j])

        #print i,j, surface.arr[i][j].state, surface.arr[i][j].h_total_pre , NS , surface.arr[i][j].inflow_tm/pixel_area , surface.arr[i][j].V_runoff/pixel_area , surface.arr[i][j].V_runoff_rill/pixel_area

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

        surface_state = surface.arr[i][j].state

        if surface_state >= 1000:
          # toto je pripraveno pro odtok v ryhach

          surface.arr[i][j].h_total_new = 0.0

          h_sub = subsurface.runoff_stream_cell(i,j)

          inflowToReach =  h_sub*pixel_area + surBIL*pixel_area
          surface.reach_inflows(id_=int(surface_state-1000),inflows=inflowToReach)

        else:
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