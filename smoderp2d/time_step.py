# @package smoderp2d.time_step methods to performe
#  time step, and to store intermeriate variables

import math
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt

import copy
import numpy as np
import time
import tensorflow as tf


from smoderp2d.core.surface import runoff
from smoderp2d.core.surface import surface_retention
from smoderp2d.io_functions import hydrographs as wf

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.003  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:

    # @tf.function
    def do_flow(self, surface, subsurface, delta_t, flow_control, courant):
        mat_efect_cont = Globals.get_mat_efect_cont_tf()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()

        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr)

        t = time.time()

        state = surface.state
        zeros = tf.zeros(state.shape, dtype=tf.float64)

        runoff_return = runoff(surface, delta_t, mat_efect_cont, zeros)
        subrunoff_return = subsurface.runoff(
            subsurface.arr, delta_t, mat_efect_cont)

        # TODO TF: Move conditions to runoff?
        surface.h_sheet = tf.where(state >= 1000, zeros, runoff_return[0])
        surface.h_rill = tf.where(state >= 1000, zeros, runoff_return[1])
        surface.h_rillPre = tf.where(state >= 1000, zeros, runoff_return[2])
        v_sheet = tf.where(state >= 1000, zeros, runoff_return[3])
        v_rill = tf.where(state >= 1000, zeros, runoff_return[4])
        rill_courant = tf.where(state >= 1000, zeros, runoff_return[5])
        surface.v_rill_rest = tf.where(state >= 1000, zeros, runoff_return[6])
        surface.vol_runoff_rill = tf.where(state >= 1000, zeros, runoff_return[7])
        surface.vol_runoff = tf.where(state >= 1000, zeros, runoff_return[8])
        surface.vol_rest = tf.where(state >= 1000, zeros, runoff_return[9])
        surface.rillWidth = tf.where(state >= 1000, zeros, runoff_return[10])
        surface.v_to_rill = tf.where(state >= 1000, zeros, runoff_return[11])

        sub_vol_runoff = tf.where(state >= 1000,
                                  subsurface.slope, subrunoff_return[0])
        sub_vol_rest = tf.where(state >= 1000,
                                subsurface.vol_rest, subrunoff_return[1])

        v = tf.math.maximum(v_sheet, v_rill)
        co = 'sheet'

        courant.CFL(surface.h_total_pre, v, delta_t, mat_efect_cont, co,
                    rill_courant)

        if subsurface.n != 0:
            subsurface.sub_vol_runoff = sub_vol_runoff
            subsurface.sub_vol_rest = sub_vol_rest

        return potRain, surface.h_sheet, surface.vol_runoff, surface.vol_rest, surface.h_rill, surface.h_rillPre, \
               surface.vol_runoff_rill, surface.v_rill_rest, surface.rillWidth, surface.v_to_rill


# self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
# courant, total_time, delta_t, combinatIndex, NoDataValue,
# sum_interception, mat_efect_cont, ratio, iter_
    def do_next_h(self, surface, subsurface, rain_arr, cumulative,
                  hydrographs, flow_control, courant, potRain, delta_t):

        global infilt_capa
        global max_infilt_capa
        global infilt_time

        rr, rc = GridGlobals.get_region_dim()
        pixel_area = GridGlobals.get_pixel_area_tf()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()

        print('infilt_capa 2x')
        print(infilt_capa)
        infilt_capa += potRain
        print(infilt_capa)
        if (infilt_capa < max_infilt_capa):
            infilt_time += delta_t
            actRain = 0.0
            # TODO: variable not used. Should we delete it?
            potRain = 0.0
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
            # print total_time-infilt_time, iii[3]*1000, k, s

        infilt.set_combinatIndex(combinatIndex)

        #
        # nulovani na zacatku kazdeho kola
        #
        surface.reset_inflows()
        surface.new_inflows()

        subsurface.fill_slope()
        subsurface.new_inflows()

        # print 'bbilll'
        potRain = tf.Variable(
            [[potRain] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
        actRain, fc.sum_interception, rain_arr.veg_true = \
            rain_f.current_rain(rain_arr, potRain, fc.sum_interception)
        surface.cur_rain = actRain

        inflow_tm_np = surface.inflow_tm.numpy()
        vol_runoff_np = surface.vol_runoff.numpy()
        vol_runoff_rill_np = surface.vol_runoff_rill.numpy()
        for i in rr:
            for j in rc[i]:
                #
                # current cell precipitation
                #

                #
                # Inflows from surroundings cells
                #
                # TODO TF: Rewrite to matrices
                inflow_tm_np[i][j] = surface.cell_runoff(i, j, vol_runoff_np,
                                                         vol_runoff_rill_np)

        surface.inflow_tm.assign(inflow_tm_np)

        #
        # Surface BILANCE
        #
        surBIL = surface.h_total_pre + actRain + surface.inflow_tm \
                 / pixel_area - (surface.vol_runoff / pixel_area +
                                 surface.vol_runoff_rill / pixel_area)


        #
        # surface retention
        #
        surBIL, surface.sur_ret, surface.cur_sur_ret = \
            surface_retention(surBIL, surface)

        zeros = tf.constant([[0] * GridGlobals.c] * GridGlobals.r,
                            dtype=tf.float64)

        exfiltration = subsurface.get_exfiltration()
        cond = exfiltration > 0
        philip_inf = infilt.philip_infiltration(surface.soil_type,
                                                surBIL)
        surBIL = tf.where(cond, surBIL, philip_inf[0])
        infiltration = tf.where(cond, zeros, philip_inf[1])
        surface.infiltration = tf.where(cond, zeros, infiltration)

        # surface retention
        surBIL += exfiltration

        surface_state = surface.state

        # toto je pripraveno pro odtok v ryhach
        cond = surface_state >= 1000
        h_sub = tf.where(cond, subsurface.runoff_stream_cell(zeros), zeros)
        inflowToReach = h_sub * pixel_area + surBIL * pixel_area
        surface.h_total_new = tf.where(cond, zeros, surBIL)

        surface_state_np = surface_state.numpy()

        for i in rr:
            for j in rc[i]:
                if surface_state_np[i, j] >= 1000:
                    # toto je pripraveno pro odtok v ryhach
                    # TODO TF: Rewrite to TF (need to change the structure of Stream)
                    surface.reach_inflows(
                        id_=int(surface_state_np[i, j] - 1000),
                        inflows=inflowToReach)

        cumulative.update_cumulative(
            surface,
            subsurface,
            delta_t)

        if not isinstance(hydrographs, wf.HydrographsPass):
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
                        actRain[i, j])

        return actRain[i, j]
