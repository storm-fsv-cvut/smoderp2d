# @package smoderp2d.time_step methods to perform
#  time step, and to store intermediate variables

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
        
        res = res.reshape(r*c)
        # for i in range(r):
        #     for j in range(c):
        #         # acumulation 
        #         res[j+i*c] += - (h_new[i][j] - h_old[i][j])/dt #m/s
    
        #         # rain 
        #         res[j+i*c] += act_rain[i][j] #m/s
        #         # sheet runoff
        #         res[j+i*c] += - tot_flow[i][j]
                
        #         # sheet inflows from neigbouring cells (try is used to avoid out of range errors)
        #         res[j+i*c] += inflow[i][j]
                    
        #         # infiltration 
        #         res[j+i*c] += - infilt[i][j] 
        #         # Surface retention
        #         res[j+i*c] +=  sur_ret[i][j]/dt   
                
        return res

    # self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
    # courant, total_time, delta_t, combinatIndex, NoDataValue,
    # sum_interception, mat_effect_cont, ratio, iter_

    def do_next_h(self, surface, subsurface, rain_arr, cumulative, 
                  hydrographs, flow_control,  potRain, delta_t,list_fd):
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
        # Until the max_infilt_capa
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


       # Calculating the actual rain
        actRain, fc.sum_interception, rain_arr.arr.veg = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
        
        surface.arr.cur_rain = actRain

        # Upacking the old water level
        h_old = np.ravel(surface.arr.h_total_pre.tolist(0))
       
        
        # Changing the actRain to a list - inserting 0 for the NoDataValues	
        act_rain = (actRain/delta_t).tolist(0)
        # Changing matrix to a single float
        dt = delta_t.mean()

        # Preparing the matrixes of flow parameters
        aa = ma.array(Globals.get_mat_aa(),mask=GridGlobals.masks)
        b = ma.array(Globals.get_mat_b(),mask=GridGlobals.masks)
        # Setting the initial guess for the solver
        h_0 = h_old 
        
         # Calculating the new water level
        soulution = sp.optimize.root(self.model, h_0, 
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
                                        method='krylov')
        
        h_new = soulution.x
        
        if soulution.success == False:
            print("Error: The solver did not converge")
            print("Objective function (worst residual) = ", max(self.model(h_new,dt,
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
                                            surface.arr.h_last_state1)))
            print("h_new = ",h_new)
        # Checking solution for negative values
        if ma.all(h_new < 0):
            raise NegativeWaterLevel()    
        # Saving the new water level
        surface.arr.h_total_new = ma.array(h_new.reshape(r,c),mask=GridGlobals.masks) 
        
        if Globals.isRill:
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
                                                surface.arr.h_last_state1)
        
            # Saving results to surface structure
            # Saving the new rill water level
            h_sheet, h_rill = compute_h_hrill(surface.arr.h_total_new, surface.arr.h_crit,
                                                        surface.arr.state,
                                                        surface.arr.h_rillPre)
            
            surface.arr.h_rill = ma.array(h_rill,mask=GridGlobals.masks)
            
            surface.arr.h_sheet = h_sheet 
            # Updating the information about rill depth
            surface.arr.h_rillPre = compute_h_rill_pre(surface.arr.h_rillPre,h_rill,
                                                       surface.arr.state)
            

                
            
            # calcualting rill runoff
            vol_to_rill = h_rill * GridGlobals.get_pixel_area()
            RILL_RATIO = 0.7
            efect_vrst = Globals.get_mat_effect_cont()
            

           
            # Calculating the rill width
            rill_h, rill_b = rill.update_hb(
            vol_to_rill, RILL_RATIO, efect_vrst, surface.arr.rillWidth)
            surface.arr.rillWidth = ma.array(ma.where(surface.arr.state > 0, rill_b,
                                            surface.arr.rillWidth),
                                            mask=GridGlobals.masks) #[m]
            
            surface.arr.vol_runoff_rill = rill_runoff(dt, 
                                                    h_rill,  efect_vrst, 
                                                    surface.arr.rillWidth) *dt # [m]

            surface.arr.vol_to_rill = ma.where(surface.arr.state > 0,vol_to_rill,
                               surface.arr.vol_to_rill)
            surface.arr.vel_rill = ma.filled(surface.arr.vol_runoff_rill/surface.arr.rillWidth/surface.arr.h_rill/dt,
                                             0.0)
        else: 
            surface.arr.h_sheet = surface.arr.h_total_new
            
        #calculating sheet runoff
        surface.arr.vol_runoff = sheet_runoff(aa, b, surface.arr.h_sheet)*dt #[m]
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
        

        return actRain
