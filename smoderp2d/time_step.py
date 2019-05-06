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

        t = time.time()

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

        tf.print('rill_courant[859, 990], v_rill[859, 990], delta_t, mat_efect_cont[859, 990], rillWidth[859, 990], surface.arr[:, :, 19][859, 990], v_to_rill[859, 990], GridGlobals.get_pixel_area(), h_rill[859, 990], surface.arr[:, :, 6][859, 990], surface.arr[:, :, 12][859, 990], state[859, 990], zeros[859, 990], v[859, 990]')
        tf.print(rill_courant[859, 990], v_rill[859, 990], delta_t, mat_efect_cont[859, 990], rillWidth[859, 990], surface.arr[:, :, 19][859, 990], v_to_rill[859, 990], GridGlobals.get_pixel_area(), h_rill[859, 990], surface.arr[:, :, 6][859, 990], surface.arr[:, :, 12][859, 990], state[859, 990], zeros[859, 990], v[859, 990])
        tf.print('potrain')
        tf.print(potRain)

        tf.print('*' * 30)
        tf.print('LOOP V time_step.doFlow:')
        tf.print(time.time() - t)

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
        print('before loop in h_next')
        for i in rr:
            for j in rc[i]:

                # print i,j, surface.arr[i][j].h_total_pre, surface.arr[i][j].vol_runoff
                #
                # current cell precipitation
                #
                actRain, fc.sum_interception, rain_arr.arr[i][j][23] = rain_f.current_rain(
                    rain_arr.arr[i][j], potRain, fc.sum_interception)
                surface.arr[i][j][3] = actRain

                #
                # Inflows from surroundings cells
                #
                surface.arr[i][j][9] = surface.cell_runoff(i, j)

                #
                # Surface BILANCE
                #
                surBIL = surface.arr[i][j][6] + actRain + surface.arr[i][j][9] / pixel_area - (
                    surface.arr[i][j][7] / pixel_area + surface.arr[i][j][17] / pixel_area)

                #
                # surface retention
                #
                surBIL = surface_retention(surBIL, surface.arr[i][j])
            
                #
                # infiltration
                #
                if subsurface.get_exfiltration(i, j) > 0:
                    surface.arr[i][j][11] = 0.0
                    infiltration = 0.0
                else:
                    surBIL, infiltration = infilt.philip_infiltration(
                        surface.arr[i][j][10], surBIL)
                    surface.arr[i][j][11] = infiltration

                # surface retention
                surBIL += subsurface.get_exfiltration(i, j)


                surface_state = surface.arr[i][j][0]

                if surface_state >= 1000:
                    # toto je pripraveno pro odtok v ryhach

                    surface.arr[i][j][5] = 0.0

                    h_sub = subsurface.runoff_stream_cell(i, j)

                    inflowToReach = h_sub * pixel_area + surBIL * pixel_area
                    
                    surface.reach_inflows(
                        id_=int(surface_state - 1000),
                        inflows=inflowToReach)

                else:
                    surface.arr[i][j][5] = surBIL

                surface_state = surface.arr[i][j][0]
                # subsurface inflow
                """
        inflow_sub = subsurface.cell_runoff(i,j,False)
        subsurface.bilance(i,j,infiltration,inflow_sub/pixel_area,delta_t)
        subsurface.fill_slope()
        """
                # if rewritten to TF, must be == changed to tf.equal()
                cumulative.update_cumulative(
                    i,
                    j,
                    surface.arr[i][j],
                    subsurface,
                    delta_t)
                hydrographs.write_hydrographs_record(
                    i,
                    j,
                    flow_control,
                    courant,
                    delta_t,
                    surface,
                    subsurface,
                    actRain)
        print('after loop in h_next')

        return actRain
