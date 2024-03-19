# @package smoderp2d.time_step methods to perform
#  time step, and to store intermediate variables

from itertools import cycle
from uu import Error
from matplotlib.pylab import norm
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infiltration
import smoderp2d.processes.rill as rill
from smoderp2d.core.surface import inflows_comp, surface_retention_impl
from smoderp2d.core.surface import surface_retention_update
from smoderp2d.core.surface import update_state1
from smoderp2d.core.surface import update_state

from smoderp2d.exceptions import NegativeWaterLevel

import numpy as np
import numpy.ma as ma
import scipy as sp
import scipy.optimize as spopt


from smoderp2d.core.surface import sheet_runoff
from smoderp2d.core.surface import rill_runoff
from smoderp2d.core.surface import compute_h_hrill
from smoderp2d.core.surface import compute_h_rill_pre


# Class manages the one time step operation

class TimeStep:
    
    def __init__(self):
        """Set the class variables to default values."""
        self.infilt_capa = 0
        self.infilt_time = 0
        self.max_infilt_capa = 0.000  # [m]

    # @staticmethod
     # objective function  
    def model(self,
                h_new,
              dt,
              h_old,
              list_fd,
              r,c,
              a,b,
              act_rain,
              soil_type,
              pixel_area,
              sur_ret_old,
              h_crit,
              state,
              rillWidth,
              h_rillPre,
              h_last_state1):
        
        h_new = ma.masked_array(h_new.reshape(r,c),mask=GridGlobals.masks)
        h_old = h_old.reshape(r,c)

        # Calculating infiltration  - function which does not allow negative levels
        infilt_buf = infiltration.philip_infiltration(soil_type,h_new)/dt #[m/s]
        infilt = ma.filled(infilt_buf,fill_value=0)
        efect_vrst = Globals.get_mat_effect_cont()
        # Calculating surface retention
        sur_ret = ma.filled(surface_retention_impl(h_new,sur_ret_old),fill_value=0) 
        # updating rill surface state
        state = update_state(h_new,h_crit,h_old,state, h_last_state1)
        if Globals.isRill and ma.any(state != 0):
            h_sheet, h_rill = compute_h_hrill(h_new,h_crit,state,h_rillPre) 
        else:
            h_sheet = h_new
            
        #calculating sheet runoff from all cells
        sheet_flow  = ma.filled(
            sheet_runoff(a,b,h_sheet),fill_value=0.0)/pixel_area
        tot_flow    = sheet_flow 
        #calculating rill runoff from all cells
        
        if  Globals.isRill and ma.any(state != 0):
            # # calcualting rill runoff
            rill_flow = ma.filled(rill_runoff(dt, h_rill,efect_vrst, rillWidth 
                                            ),fill_value=0.0)/pixel_area # [m/s]

            tot_flow += rill_flow
            
        tot_flow = np.nan_to_num(tot_flow,0.0)
        
        # calculating inflows from neigbouring cells
        inflow = inflows_comp(tot_flow, list_fd)
            
        h_new = ma.filled(h_new,fill_value=0.0)
        # setting all residuals to zero
        res = np.zeros((r,c))
        # calculating residual for each cell - adding contributions from all processes
        
        # acumulation
        res = - (h_new - h_old)/dt #m/s
        # rain
        res += act_rain
        # runoff - outflow
        res += - tot_flow
        # inflow from neigbouring cells
        res += inflow
        # infiltration
        res += - infilt
        # Surface retention
        res += sur_ret/dt
        
        res = res.ravel()         
        return res

    # self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
    # courant, total_time, delta_t, combinatIndex, NoDataValue,
    # sum_interception, mat_effect_cont, ratio, iter_

    def do_next_h(self, surface, subsurface, rain_arr, cumulative, 
                  hydrographs, flow_control,   delta_t,  delta_tmax,list_fd):
        # global variables for infilitration
        # class infilt_capa
        # global max_infilt_capa
        # global infilt_time
        # parameters
        r, c = GridGlobals.r, GridGlobals.c
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()
        # Calculating the infiltration
        sr = Globals.get_sr()
        itera = Globals.get_itera()
        
        # Until the max_infilt_capa
        potRain, tz_temp = rain_f.timestepRainfall(
            itera, flow_control.total_time+delta_t, delta_t, flow_control.tz, sr
            )
        self.infilt_capa += potRain
        if ma.all(self.infilt_capa < self.max_infilt_capa):
            self.infilt_time += delta_t
            actRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            potRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            return actRain

        


        
        # Upacking the old water level
        h_old = np.ravel(surface.arr.h_total_pre.tolist(0))

        # Preparing the matrixes of flow parameters
        aa = ma.array(Globals.get_mat_aa(),mask=GridGlobals.masks)
        b = ma.array(Globals.get_mat_b(),mask=GridGlobals.masks)
        # Setting the initial guess for the solver
        h_0 = h_old 

        dh_max = 1e-5  # [m]
        
        # Setting the maximum number of iterations for the solver
        max_iter = 20

        # Calculating the new water level
        for i in range(1, fc.max_iter ):
            # Calcualting the potenial rain
            potRain, tz_temp = rain_f.timestepRainfall(
            itera, flow_control.total_time+delta_t, delta_t, flow_control.tz, sr
            )
            
            # Calculating the actual rain
            actRain, sum_interception_temp, vegaarr_temp = \
                rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
            
            # Changing the actRain to a list - inserting 0 for the NoDataValues	
            act_rain = (actRain/delta_t).tolist(0)
            # After the max_infilt_capa is filled       
            for iii in combinatIndex:
                # TODO: variable not used. Should we delete it?
                index = iii[0]
                k = iii[1]
                s = iii[2]
                
                iii[3] = infiltration.philip_implicit(
                    k,
                    s,
                    delta_t,
                    fc.total_time + delta_t -  self.infilt_time,
                    NoDataValue)
            
            infiltration.set_combinatIndex(combinatIndex)
             
           
            # Changing matrix to a single float
            dt = delta_t.mean()
            try:
                solution = sp.optimize.root(self.model, h_0, 
                                            args=(dt,
                                                    h_old,
                                                    list_fd,
                                                    r,c,
                                                    aa,b,
                                                    act_rain,
                                                    surface.arr.soil_type,
                                                    pixel_area,
                                                    surface.arr.sur_ret,
                                                    surface.arr.h_crit,
                                                    surface.arr.state,
                                                    surface.arr.rillWidth,
                                                    surface.arr.h_rillPre,
                                                    surface.arr.h_last_state1),
                                                method='krylov', options={'fatol':1e-8,'maxiter':max_iter})
                
                h_new = solution.x
                
                #print ('h_hew {} nit {}'.format(h_new.mean(), solution.nit))
                if solution.success == False or solution.nit > max_iter-1:
                    delta_t = delta_t/2
                    print('now')
                    continue
            except ZeroDivisionError:
                raise Error("Error: The nonlinear solver did not converge. Try to change the time step")
            if solution.nit > 4 :
            #if ma.any(abs(h_new - h_old) > dh_max):
                delta_t = delta_t/2
            else:
                # print ('break dt {}'.format(dt))
                if solution.nit < 3 : 
                    if ma.all(delta_t*2 < delta_tmax):
                        delta_t = delta_t*2
                    else:
                        delta_t = delta_tmax
                break

                
        #input('press...')
        if i == fc.max_iter-1:
            print(abs(h_new - h_old))
            raise Error("Error: The nonlinear solver did not meet the requirements after repeated decreasing of the time step. Try to change the maximum time step.")        
        
        # Checking solution for negative values
        if ma.all(h_new < 0):
            raise NegativeWaterLevel()   
        
        # saving the actual rain at current time step
        # save the tz for actual time step
        
        potRain, flow_control.tz = rain_f.timestepRainfall(
        itera, flow_control.total_time+delta_t, delta_t, flow_control.tz, sr
        )
        # Calculating the actual rain
        actRain, fc.sum_interception, rain_arr.arr.veg = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
        
        surface.arr.cur_rain = actRain 
        # Saving the new water level
        surface.arr.h_total_new = ma.array(h_new.reshape(r,c),mask=GridGlobals.masks) 
        # Saving the actual rain
        surface.arr.cur_rain = actRain  
        surface.arr.h_total_new = ma.array(h_new.reshape(r,c),mask=GridGlobals.masks)  
        # Saving the actual rain
        surface.arr.cur_rain = actRain  
        if Globals.isRill:
            last_state1_buf = surface.arr.h_last_state1
            #saving the last value of the water level in rill during growing phase (state = 1)
            # enables to restart the growing phase (switch from 2 to 1)
            state_1_cond = ma.logical_and(
                    surface.arr.state == 1,
                    surface.arr.h_total_new < surface.arr.h_total_pre,
                )
            surface.arr.h_last_state1 = ma.where(
                    state_1_cond,
                    surface.arr.h_total_pre,
                    surface.arr.h_last_state1
                ) 
        # updating rill surface state
            surface.arr.state = update_state(surface.arr.h_total_new,
                                                surface.arr.h_crit,
                                                surface.arr.h_total_pre,
                                                surface.arr.state,
                                                last_state1_buf)
        
            # Saving results to surface structure
            # Saving the new rill water level
            h_sheet, h_rill = compute_h_hrill(surface.arr.h_total_new, surface.arr.h_crit,
                                                        surface.arr.state,
                                                        surface.arr.h_rillPre)
            
            surface.arr.h_rill = ma.array(h_rill,mask=GridGlobals.masks)
            
            surface.arr.h_sheet = ma.array(h_sheet,mask=GridGlobals.masks) 
            # Updating the information about rill depth
            surface.arr.h_rillPre = compute_h_rill_pre(surface.arr.h_rillPre,h_rill,
                                                       surface.arr.state)
            

                
            
            # calcualting rill runoff
            vol_to_rill = h_rill * GridGlobals.get_pixel_area()
            RILL_RATIO = 0.7
            efect_vrst = Globals.get_mat_effect_cont()

            surface.arr.vol_runoff_rill = ma.filled(rill_runoff(dt, 
                                                    surface.arr.h_rill,  efect_vrst, 
                                                    surface.arr.rillWidth),
                                                  0)*dt # [m]
            
            surface.arr.vol_to_rill = ma.where(surface.arr.state > 0,vol_to_rill,
                               surface.arr.vol_to_rill)
            surface.arr.vel_rill = ma.filled(surface.arr.vol_runoff_rill/surface.arr.rillWidth/surface.arr.h_rill/dt,
                                             0.0)
            # Calculating the rill width
            rill_h, rill_b = rill.update_hb(
            vol_to_rill, RILL_RATIO, efect_vrst, surface.arr.rillWidth)
            surface.arr.rillWidth = ma.array(ma.where(surface.arr.state > 0, rill_b,
                                            surface.arr.rillWidth),
                                            mask=GridGlobals.masks) #[m]
            
        else: 
            surface.arr.h_sheet = surface.arr.h_total_new
        
        #calculating sheet runoff
        surface.arr.vol_runoff = ma.filled(sheet_runoff(aa, b, surface.arr.h_sheet),fill_value=0.0)*dt #[m]
    
        # Saving the inflows
        tot_flow = (surface.arr.vol_runoff + surface.arr.vol_runoff_rill)
        
        surface.arr.inflow_tm =ma.array(inflows_comp(tot_flow, list_fd),mask=GridGlobals.masks)
        
        # Calculating the infiltration
        surface.arr.infiltration = infiltration.philip_infiltration(surface.arr.soil_type,
                                                                    surface.arr.h_total_new) #[m]    
        
        # Updating surface retention
        h_ret = actRain - surface.arr.infiltration
        surface_retention_update(h_ret,surface.arr)
        

        cumulative.update_cumulative(
            surface.arr,
            subsurface.arr,
            delta_t)
        

        return actRain, delta_t
