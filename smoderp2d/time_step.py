# @package smoderp2d.time_step methods to performe
#  time step, and to store intermeriate variables

import math
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt

import copy
import numpy as np
import numpy.ma as ma


from smoderp2d.core.surface import runoff
from smoderp2d.core.surface import surface_retention

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.000  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:

    def do_flow(self, surface, subsurface, delta_t, flow_control, courant):
        rr, rc = GridGlobals.get_region_dim()
        mat_efect_cont = Globals.get_mat_efect_cont()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()

        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr
        )

        surface_state = surface.arr.state
        h_total_pre = surface.arr.h_total_pre

        runoff_return = runoff(
            surface.arr, delta_t, mat_efect_cont, fc.ratio
        )
        subrunoff_return = subsurface.runoff(
            delta_t, mat_efect_cont
        )

        cond_state_flow = surface_state > Globals.streams_flow_inc
        q_sheet = ma.where(cond_state_flow, 0, runoff_return[0])
        v_sheet = ma.where(cond_state_flow, 0, runoff_return[1])
        q_rill = ma.where(cond_state_flow, 0, runoff_return[2])
        v_rill = ma.where(cond_state_flow, 0, runoff_return[3])
        if np.any(cond_state_flow):
            fc.ratio = 0
        else:
            # TODO: Better way to make it just a number
            fc.ratio = runoff_return[4]
        rill_courant = ma.where(cond_state_flow, 0, runoff_return[5])

        q_surface = q_sheet + q_rill
        v = np.maximum(v_sheet, v_rill)
        co = 'sheet'

        courant.CFL(
            surface.arr.h_total_pre,
            v,
            delta_t,
            mat_efect_cont,
            co,
            rill_courant
        )
        rill_courant = 0.
                # w1 = surface.arr.get_item([i, j]).vol_runoff_rill
                # w2 = surface.arr.get_item([i, j]).v_rill_rest

        # in TF, return potRain, surface.h_sheet, surface.vol_runoff, surface.vol_rest, surface.h_rill, surface.h_rillPre, \
        #                surface.vol_runoff_rill, surface.v_rill_rest, surface.rillWidth, surface.v_to_rill
        return potRain

        # in TF,         if subsurface.n != 0:
        #             subsurface.sub_vol_runoff = sub_vol_runoff
        #             subsurface.sub_vol_rest = sub_vol_rest


# self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
# courant, total_time, delta_t, combinatIndex, NoDataValue,
# sum_interception, mat_efect_cont, ratio, iter_
    def do_next_h(self, surface, subsurface, rain_arr, cumulative,
                  hydrographs, flow_control, courant, potRain, delta_t):

        global infilt_capa
        global max_infilt_capa
        global infilt_time

        rr, rc = GridGlobals.get_region_dim()
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()

        masks = [[True] * GridGlobals.c for _ in range(GridGlobals.r)]
        rr, rc = GridGlobals.get_region_dim()
        for r_c_index in range(len(rr)):
            for c in rc[r_c_index]:
                masks[rr[r_c_index]][c] = False

        infilt_capa += potRain
        if np.all(infilt_capa < max_infilt_capa):
            infilt_time += delta_t
            actRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=masks
            )
            potRain = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=masks
            )
            for i in rr:
                for j in rc[i]:
                    hydrographs.write_hydrographs_record(
                        i,
                        j,
                        flow_control,
                        courant,
                        delta_t,
                        surface,
                        subsurface,
                        cumulative,
                        actRain)
            return actRain

        for iii in combinatIndex:
            # TODO: variable not used. Should we delete it?
            index = iii[0]
            k = iii[1]
            s = iii[2]
            # jj * 100.0 !!! smazat
            iii[3] = infilt.phlilip(
                k,
                s,
                delta_t,
                fc.total_time - infilt_time,
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

        #
        # Surface BILANCE
        #
        surBIL = surface.arr.h_total_pre + actRain + surface.arr.inflow_tm / \
                 pixel_area - (surface.arr.vol_runoff / pixel_area +
                               surface.arr.vol_runoff_rill / pixel_area)

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
        surface.infiltration = ma.where(
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

        surface.arr.h_total_new = ma.where(
            surface_state > Globals.streams_flow_inc,  # stream flow in the cell
            0,
            surBIL
        )
        # h_sub = subsurface.runoff_stream_cell(i, j)
        #
        #                     inflowToReach = h_sub * pixel_area + surBIL * pixel_area
        #
        #                     surface.reach_inflows(
        #                         surface_state - Globals.streams_flow_inc,
        #                         inflowToReach)

        surface_state = surface.arr.state

        # subsurface inflow
        """
        inflow_sub = subsurface.cell_runoff(i,j,False)
        subsurface.bilance(i,j,infiltration,inflow_sub/pixel_area,delta_t)
        subsurface.fill_slope()
        """

        cumulative.update_cumulative(
            surface.arr,
            subsurface.arr,
            delta_t)
        for i in rr:
            for j in rc[i]:
                hydrographs.write_hydrographs_record(
                    i,
                    j,
                    flow_control,
                    courant,
                    delta_t,
                    surface,
                    subsurface.arr,
                    cumulative,
                    actRain)

        return actRain
