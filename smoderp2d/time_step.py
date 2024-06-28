# @package smoderp2d.time_step methods to perform
#  time step, and to store intermediate variables


from re import sub
from textwrap import fill
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt
import smoderp2d.processes.rill as rill
from smoderp2d.core.surface import (
    runoff, sheet_runoff, rill_runoff, compute_h_hrill, surface_retention,
    inflows_comp, surface_retention_update, update_state
)

from smoderp2d.exceptions import NegativeWaterLevel

import numpy as np
import numpy.ma as ma


# Class manages the one time step operation

class TimeStep:
    """TODO."""

    def __init__(self):
        """Set the class variables to default values."""
        self.infilt_capa = 0
        self.infilt_time = 0
        self.max_infilt_capa = 0.000  # [m]

    @staticmethod
    def do_flow(surface, subsurface, delta_t, flow_control, courant):
        """TODO.

        :param surface: TODO
        :param subsurface: TODO
        :param delta_t: current time step length
        :param flow_control: TODO
        :param courant: TODO
        """
        mat_effect_cont = Globals.get_mat_effect_cont()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()

        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr
        )

        surface_state = surface.arr.state

        runoff_return = runoff(surface.arr, delta_t, mat_effect_cont)

        cond_state_flow = surface_state > Globals.streams_flow_inc
        v_sheet = ma.where(cond_state_flow, 0, runoff_return[0])
        v_rill = ma.where(cond_state_flow, 0, runoff_return[1])
        subsurface.runoff(delta_t, mat_effect_cont, cond_state_flow)

        rill_courant = ma.where(cond_state_flow, 0, runoff_return[2])

        surface.arr.h_sheet = ma.where(
            cond_state_flow, surface.arr.h_sheet, runoff_return[3]
        )
        surface.arr.h_rill = ma.where(
            cond_state_flow, surface.arr.h_rill, runoff_return[4]
        )
        surface.arr.h_rillPre = ma.where(
            cond_state_flow, surface.arr.h_rillPre, runoff_return[5]
        )
        surface.arr.vol_runoff = ma.where(
            cond_state_flow, surface.arr.vol_runoff, runoff_return[6]
        )
        surface.arr.vol_rest = ma.where(
            cond_state_flow, surface.arr.vol_rest, runoff_return[7]
        )
        surface.arr.v_rill_rest = ma.where(
            cond_state_flow, surface.arr.v_rill_rest, runoff_return[8]
        )
        surface.arr.vol_runoff_rill = ma.where(
            cond_state_flow, surface.arr.vol_runoff_rill, runoff_return[9]
        )
        surface.arr.vel_rill = ma.where(
            cond_state_flow, surface.arr.vel_rill, runoff_return[10]
        )

        v = ma.maximum(v_sheet, v_rill)
        co = 'sheet'
        courant.CFL(
            v,
            delta_t,
            mat_effect_cont,
            co,
            rill_courant
        )
        # w1 = surface.arr.get_item([i, j]).vol_runoff_rill
        # w2 = surface.arr.get_item([i, j]).v_rill_rest

        return potRain

    def do_next_h(self, surface, subsurface, rain_arr, cumulative, hydrographs,
                  flow_control, courant, potRain, delta_t):
        """TODO.

        :param surface: TODO
        :param subsurface: TODO
        :param rain_arr: TODO
        :param cumulative: TODO
        :param hydrographs: TODO
        :param flow_control: TODO
        :param courant: TODO
        :param potRain: TODO
        :param delta_t: current time step length
        """
        rr, rc = GridGlobals.get_region_dim()
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()

        self.infilt_capa += potRain
        if ma.all(self.infilt_capa < self.max_infilt_capa):
            self.infilt_time += delta_t
            actRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
            hydrographs.write_hydrographs_record(
                None,
                None,
                flow_control,
                courant,
                delta_t,
                surface,
                subsurface,
                cumulative,
                actRain)
            return actRain

        for iii in combinatIndex:
            k = iii[1]
            s = iii[2]
            # jj * 100.0 !!! smazat
            iii[3] = infilt.philip(
                k,
                s,
                delta_t,
                fc.total_time - self.infilt_time,
                NoDataValue)

        infilt.set_combinatIndex(combinatIndex)

        #
        # nulovani na zacatku kazdeho kola
        #
        surface.reset_inflows()
        surface.new_inflows()

        subsurface.fill_slope()
        subsurface.new_inflows()

        #
        # current cell precipitation
        #
        actRain, fc.sum_interception, rain_arr.arr.veg = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
        surface.arr.cur_rain = actRain

        #
        # Inflows from surroundings cells
        #
        for i in rr:
            for j in rc[i]:
                surface.arr.inflow_tm[i, j] = surface.cell_runoff(i, j)
                subsurface.arr.inflow_tm[i, j] = subsurface.cell_runoff(i, j)


        #
        # Surface water balance 
        #
        surBIL = (
            surface.arr.h_total_pre + actRain + surface.arr.inflow_tm /
            pixel_area - (
                surface.arr.vol_runoff / pixel_area +
                surface.arr.vol_runoff_rill / pixel_area
            )
        )

        #
        # infiltration
        #
        philip_infiltration = infilt.philip_infiltration(
            surface.arr.soil_type, surBIL
        )
        surBIL = ma.where(
            subsurface.get_exfiltration() > 0,
            surBIL,
            philip_infiltration[0]
        )
        surface.arr.infiltration = ma.where(
            subsurface.get_exfiltration() > 0,
            0,
            philip_infiltration[1]
        )

        #
        # surface retention
        #
        surBIL = surface_retention(surBIL, surface.arr)

        # add exfiltration
        surBIL += subsurface.get_exfiltration()

        surface_state = surface.arr.state

        state_condition = surface_state > Globals.streams_flow_inc
        surface.arr.h_total_new = ma.where(
            state_condition,  # stream flow in the cell
            0,
            surBIL
        )
        if ma.any(surface_state > Globals.streams_flow_inc):
            h_sub = subsurface.runoff_stream_cell(state_condition)
            inflowToReach = ma.where(
                state_condition,
                h_sub * pixel_area + surBIL * pixel_area,
                0
            )
            surface.reach_inflows(
                surface_state - Globals.streams_flow_inc,
                inflowToReach,
                state_condition
            )

        # subsurface water balance
        subsurface.balance(surface.arr.infiltration,delta_t)
        subsurface.fill_slope()

        cumulative.update_cumulative(
            surface.arr,
            subsurface.arr,
            delta_t)
        hydrographs.write_hydrographs_record(
            None,
            None,
            flow_control,
            courant,
            delta_t,
            surface,
            subsurface,
            cumulative,
            actRain)

        return actRain

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
              surface,
              h_crit,
              state,
              rillWidth,
              h_rillPre,
              h_last_state1,
              exfiltration):
        
        h_new = ma.masked_array(h_new.reshape(r,c),mask=GridGlobals.masks)
        h_old = h_old.reshape(r,c)

        # Calculating infiltration  - function which does not allow negative levels
        _bil,infilt_buf = infilt.philip_infiltration(soil_type, h_new) #[m]
        infiltr = ma.filled(ma.where(exfiltration > 0,
                                     0,
                                     infilt_buf),
                                    fill_value=0)/dt #[m/s]
        efect_vrst = Globals.get_mat_effect_cont()
        # Calculating surface retention
        sur_ret = ma.filled(surface_retention(h_new,surface),fill_value=0)
        if Globals.isRill: 
            # updating rill surface state
            state, _ = update_state(h_new,h_crit,h_old,state, h_last_state1)
        if Globals.isRill and ma.any(state != 0):
            h_sheet, h_rill, _h_rill_pre = compute_h_hrill(h_new,h_crit,state,h_rillPre) 
        else:
            h_sheet = h_new
            
        #calculating sheet runoff from all cells
        _q_sheet, vol_runoff, _volrest = sheet_runoff(dt, a, b, h_sheet) #[m^3]
        sheet_flow  = ma.filled(vol_runoff,fill_value=0.0)/pixel_area/dt # [m/s]
        tot_flow    = sheet_flow 
        #calculating rill runoff from all cells
        
        if  Globals.isRill and ma.any(state != 0):
            # # calcualting rill runoff
            _v_rill, _v_rill_rest, vol_runoff_rill, _courant, _vol_to_rill, _b = rill_runoff(
                dt, efect_vrst, h_rill, rillWidth)
            rill_flow = ma.filled(vol_runoff_rill,fill_value=0.0)/pixel_area/dt # [m/s]

            tot_flow += rill_flow
            
        tot_flow = np.nan_to_num(tot_flow,0.0)
        
        # calculating inflows from neigbouring cells
        inflow = inflows_comp(tot_flow, list_fd)
            
        h_new = ma.filled(h_new,fill_value=0.0)
        
        exfiltration = ma.filled(exfiltration,fill_value=0.0)
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
        res += - infiltr
        # Surface retention
        res += sur_ret/dt
        # exfiltration
        res += exfiltration/dt
        
        res = res.ravel()         
        return res

    # self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
    # courant, total_time, delta_t, combinatIndex, NoDataValue,
    # sum_interception, mat_effect_cont, iter_
    def do_next_h_implicit(self, surface, subsurface, rain_arr, cumulative,
                           hydrographs, flow_control, delta_t, delta_tmax,
                           list_fd,courant):
        """TODO.

        :param surface: TODO
        :param subsurface: TODO
        :param rain_arr: TODO
        :param cumulative: TODO
        :param hydrographs: TODO
        :param flow_control: TODO
        :param courant: TODO
        :param potRain: TODO
        :param delta_t: current time step length
        """
        import scipy.optimize as spopt

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
            itera, fc.total_time, delta_t, fc.tz, sr
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
        aa = ma.array(Globals.get_mat_aa(), mask=GridGlobals.masks)
        b = ma.array(Globals.get_mat_b(), mask=GridGlobals.masks)
        # Setting the initial guess for the solver
        h_0 = h_old 

        # Setting the maximum number of iterations for the solver
        max_iter = 20
        min_iter = 10
        # parameter for the time step modification  
        modif_up = 2
        modif_down = 2
        # Calculating the new water level
        for i in range(1, fc.max_iter ):
            # Calcualting the potenial rain
            potRain, tz_temp = rain_f.timestepRainfall(
                itera, flow_control.total_time, delta_t, flow_control.tz, sr
            )

            # Calculating the actual rain
            actRain, sum_interception_temp, vegaarr_temp = \
                rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)

            # Changing the actRain to a list - inserting 0 for the NoDataValues	
            act_rain = (actRain / delta_t).tolist(0)
            # After the max_infilt_capa is filled       
            for iii in combinatIndex:
                # TODO: variable not used. Should we delete it?
                index = iii[0]
                k = iii[1]
                s = iii[2]

                iii[3] = infilt.philip(
                    k,
                    s,
                    delta_t,
                    fc.total_time + delta_t -  self.infilt_time,
                    NoDataValue)

            infilt.set_combinatIndex(combinatIndex)

            def model_args(h_new):
                res = self.model(
                    h_new,
                    delta_t,
                    h_old,
                    list_fd,
                    r,c,
                    aa,b,
                    act_rain,
                    surface.arr.soil_type,
                    pixel_area,
                    surface.arr,
                    surface.arr.h_crit,
                    surface.arr.state,
                    surface.arr.rillWidth,
                    surface.arr.h_rillPre,
                    surface.arr.h_last_state1,
                    subsurface.get_exfiltration()
                )
                return res
            try:
                solution = spopt.root(
                    model_args, h_0, method='df-sane',
                    options={'fatol':1e-4, 'maxiter': max_iter}
                )

                h_new = solution.x
                fc.iter_ = solution.nit

                if solution.success == False:
                    delta_t = delta_t / modif_down
                    continue

            except ZeroDivisionError:
                raise "Error: The nonlinear solver did not converge. Try to change the time step"

            if solution.nit >= max_iter:
            #if ma.any(abs(h_new - h_old) > dh_max):
                delta_t = delta_t / modif_down
            else:
                # print ('break dt {}'.format(dt))
                if solution.nit < min_iter : 
                    if ma.all(delta_t * modif_up < delta_tmax):
                        delta_t = delta_t * modif_up
                    else:
                        delta_t = delta_tmax
                break

        if i == fc.max_iter - 1:
            raise "Error: The nonlinear solver did not meet the requirements after repeated decreasing of the time step. Try to change the maximum time step."       

        # Checking solution for negative values
        if ma.all(h_new < 0):
            raise NegativeWaterLevel()   
        #---------------------------------------------------------------------
        # POSTPROCESSING
        #---------------------------------------------------------------------
        surface.reset_inflows()
        surface.new_inflows()

        subsurface.fill_slope()
        subsurface.new_inflows()

        surface_state = surface.arr.state

        state_condition = surface_state > Globals.streams_flow_inc
        # Saving the new water level
        surface.arr.h_total_new = ma.where(
            state_condition,  # stream flow in the cell
            0,
            h_new.reshape(r, c))
        # saving the actual rain at current time step
        # save the tz for actual time step
        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr
        )
        # Calculating the actual rain
        actRain, fc.sum_interception, rain_arr.arr.veg = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)

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
            surface.arr.state, _ = update_state(
                surface.arr.h_total_new,
                surface.arr.h_crit,
                surface.arr.h_total_pre,
                surface.arr.state,
                last_state1_buf
            )

            # Saving results to surface structure
            # Saving the new rill water level
            h_sheet, h_rill, h_rill_pre = compute_h_hrill(
                surface.arr.h_total_new,
                surface.arr.h_crit,
                surface.arr.state,
                surface.arr.h_rillPre
            )

            surface.arr.h_rill = ma.array(h_rill, mask=GridGlobals.masks)

            surface.arr.h_sheet = ma.array(h_sheet, mask=GridGlobals.masks)

            surface.arr.h_rillPre = ma.array(h_rill_pre, mask=GridGlobals.masks)

            # calcualting rill runoff
            # vol_to_rill = h_rill * GridGlobals.get_pixel_area()
            efect_vrst = Globals.get_mat_effect_cont()

            v_rill, v_rill_rest, vol_runoff_rill, _courant, vol_to_rill, rill_b = rill_runoff(
                delta_t, efect_vrst, h_rill, surface.arr.rillWidth
            )

            surface.arr.vol_runoff_rill = vol_runoff_rill  # [m]

            surface.arr.vol_to_rill = vol_to_rill
            surface.arr.vel_rill = ma.filled(v_rill, fill_value=0.0)
            surface.arr.rillWidth = ma.array(
                ma.where(surface.arr.state > 0, rill_b, surface.arr.rillWidth),
                mask=GridGlobals.masks
            )  #[m]
            surface.arr.v_rill_rest = ma.filled(v_rill_rest, fill_value=0.0)
        else: 
            # Saving the new water level
            surface.arr.h_sheet = surface.arr.h_total_new

        #calculating sheet runoff
        _q_sheet, surface.arr.vol_runoff, surface.arr.vol_rest = ma.filled(
            sheet_runoff(delta_t, aa, b, surface.arr.h_sheet), fill_value=0.0
        )

        # Saving the inflows
        tot_flow = (surface.arr.vol_runoff + surface.arr.vol_runoff_rill)

        surface.arr.inflow_tm =ma.array(inflows_comp(tot_flow, list_fd), mask=GridGlobals.masks)

        # Calculating the infiltration
        _bil,infiltration = infilt.philip_infiltration(
            surface.arr.soil_type, surface.arr.h_total_new
        ) #[m]
        surface.arr.infiltration = ma.where(
            subsurface.get_exfiltration() > 0, 0, infiltration
        )
        # Updating surface retention
        h_ret = actRain - surface.arr.infiltration
        surface_retention_update(h_ret, surface.arr)

        #Reaches

        if ma.any(surface_state > Globals.streams_flow_inc):
            h_sub = subsurface.runoff_stream_cell(state_condition)
            inflowToReach = ma.where(
                state_condition,
                h_sub * pixel_area + h_new.reshape(r, c) * pixel_area,
                0
            )
            surface.reach_inflows(
                surface_state - Globals.streams_flow_inc,
                inflowToReach,
                state_condition
            )

        cumulative.update_cumulative(
            surface.arr,
            subsurface.arr,
            delta_t
        )

        hydrographs.write_hydrographs_record(
            None,
            None,
            flow_control,
            courant,
            delta_t,
            surface,
            subsurface,
            cumulative,
            actRain
        )

        return actRain, delta_t
