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
        rr, rc = GridGlobals.get_region_dim_tf()
        mat_efect_cont = Globals.get_mat_efect_cont_tf()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()

        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr)

        state = surface.arr[:, :, 0]
        zeros = tf.zeros(state.shape, dtype=tf.float32)

        runoff_return = runoff(surface, delta_t, mat_efect_cont, zeros)
        subrunoff_return = subsurface.runoff(
            subsurface.arr, delta_t, mat_efect_cont)

        # TODO TF: Move conditions to runoff?
        h_sheet = tf.where(state >= 1000, zeros, runoff_return[0])
        h_rill = tf.where(state >= 1000, zeros, runoff_return[1])
        h_rill_pre = tf.where(state >= 1000, zeros, runoff_return[2])
        v_sheet = tf.where(state >= 1000, zeros, runoff_return[3])
        v_rill = tf.where(state >= 1000, zeros, runoff_return[4])
        rill_courant = tf.where(state >= 1000, zeros, runoff_return[5])
        v_rill_rest = tf.where(state >= 1000, zeros, runoff_return[6])
        vol_runoff_rill = tf.where(state >= 1000, zeros, runoff_return[7])
        vol_runoff = tf.where(state >= 1000, zeros, runoff_return[8])
        vol_rest = tf.where(state >= 1000, zeros, runoff_return[9])
        rillWidth = tf.where(state >= 1000, zeros, runoff_return[10])
        v_to_rill = tf.where(state >= 1000, zeros, runoff_return[11])

        sub_vol_runoff = tf.where(state >= 1000,
                                  subsurface.arr[:, :, 4], subrunoff_return[0])
        sub_vol_rest = tf.where(state >= 1000,
                                subsurface.arr[:, :, 8], subrunoff_return[1])

        v = tf.math.maximum(v_sheet, v_rill)
        co = 'sheet'

        courant.CFL(surface.arr[:, :, 6], v, delta_t, mat_efect_cont, co,
                    rill_courant)

        if subsurface.n != 0:
            subsurface.arr.assign(tf.stack([subsurface.arr[:, :, 0],
                                    subsurface.arr[:, :, 1],
                                    subsurface.arr[:, :, 2],
                                    subsurface.arr[:, :, 3],
                                    subsurface.arr[:, :, 4],
                                    subsurface.arr[:, :, 5],
                                    sub_vol_runoff,
                                    subsurface.arr[:, :, 7], #####
                                    sub_vol_rest,
                                    subsurface.arr[:, :, 9],
                                    subsurface.arr[:, :, 10],
                                    subsurface.arr[:, :, 11],
                                    subsurface.arr[:, :, 12],
                                    subsurface.arr[:, :, 13]], 2))

        return potRain, h_sheet, vol_runoff, vol_rest, h_rill, h_rill_pre, \
               vol_runoff_rill, v_rill_rest, rillWidth, v_to_rill


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
            [[potRain] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
        actRain, fc.sum_interception, rain_arr.arr[:, :, 23] = \
            rain_f.current_rain(rain_arr.arr, potRain, fc.sum_interception)
        surface.arr[:, :, 3] = actRain

        for i in rr:
            for j in rc[i]:
                #
                # current cell precipitation
                #

                #
                # Inflows from surroundings cells
                #
                # TODO TF: Rewrite to matrices
                surface.arr[i][j][9] = surface.cell_runoff(i, j)

        #
        # Surface BILANCE
        #
        surBIL = surface.arr[:, :, 6] + actRain + surface.arr[:, :, 9] \
                 / pixel_area - (surface.arr[:, :, 7] / pixel_area +
                                 surface.arr[:, :, 17] / pixel_area)

        #
        # surface retention
        #
        surBIL, surface.arr[:, :, 1], surface.arr[:, :, 2] = \
            surface_retention(surBIL, surface.arr)

        zeros = tf.constant([[0] * GridGlobals.c] * GridGlobals.r,
                            dtype=tf.float32)

        exfiltration = subsurface.get_exfiltration()
        cond = exfiltration > 0
        philip_inf = infilt.philip_infiltration(surface.arr[:, :, 10],
                                                surBIL)
        surBIL = tf.where(cond, surBIL, philip_inf[0])
        infiltration = tf.where(cond, zeros, philip_inf[1])
        surface.arr[:, :, 11] = tf.where(cond, zeros, infiltration)

        # surface retention
        surBIL += exfiltration

        surface_state = surface.arr[:, :, 0]
        surface.arr[:, :, 5] = zeros

        # toto je pripraveno pro odtok v ryhach
        cond = surface_state >= 1000
        h_sub = tf.where(cond, subsurface.runoff_stream_cell(zeros), zeros)
        inflowToReach = h_sub * pixel_area + surBIL * pixel_area
        surface.arr[:, :, 5] = tf.where(cond, surface.arr[:, :, 5], surBIL)

        for i in rr:
            for j in rc[i]:
                if surface_state[i, j] >= 1000:
                    # toto je pripraveno pro odtok v ryhach
                    # TODO TF: Rewrite to TF (need to change the structure of Stream)
                    surface.reach_inflows(
                        id_=int(surface_state[i, j] - 1000),
                        inflows=inflowToReach)

        cumulative.update_cumulative(
            surface.arr,
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
        print('after loop in h_next')

        return actRain[i, j]
