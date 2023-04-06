# @package smoderp2d.time_step methods to performe
#  time step, and to store intermeriate variables

import math
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt

import copy
import numpy as np
import scipy as sp

from smoderp2d.core.surface import runoff
from smoderp2d.core.surface import surface_retention

from smoderp2d.core.general import Globals, GridGlobals


infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.000  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:
    " The function do_flow will be probably not used for implicit method."
    def do_flow(self, surface, subsurface, delta_t, flow_control, courant):
        rr, rc = GridGlobals.get_region_dim()
        mat_efect_cont = Globals.get_mat_efect_cont()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()

        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr
        )

        for i in rr:
            for j in rc[i]:
                # TODO: variable not used. Should we delete it?
                h_total_pre = surface.arr.get_item([i, j]).h_total_pre

                surface_state = surface.arr.get_item([i, j]).state

                if surface_state > Globals.streams_flow_inc:
                    q_sheet = 0.0
                    v_sheet = 0.0
                    q_rill = 0.0
                    v_rill = 0.0
                    rill_courant = 0.0
                else:
                    q_sheet, v_sheet, q_rill, v_rill, fc.ratio, rill_courant = runoff(
                        i, j, surface.arr.get_item([i, j]), delta_t, mat_efect_cont[i][j], fc.ratio
                    )
                    subsurface.runoff(i, j, delta_t, mat_efect_cont[i][j])

                # TODO: variable not used. Should we delete it?
                q_surface = q_sheet + q_rill
                v = max(v_sheet, v_rill)
                co = 'sheet'
                courant.CFL(
                    i,
                    j,
                    surface.arr.get_item([i, j]).h_total_pre,
                    v,
                    delta_t,
                    mat_efect_cont[i][j],
                    co,
                    rill_courant)
                # TODO: variable not used. Should we delet it?
                rill_courant = 0.

                # w1 = surface.arr.get_item([i, j]).vol_runoff_rill
                # w2 = surface.arr.get_item([i, j]).v_rill_rest

        return potRain


# self,surface,  rain_arr, cumulative, hydrographs, potRain,
#  total_time, delta_t, 
# sum_interception, mat_efect_cont, ratio, iter_
    def level_balance(self, h_new,
                      # from this are load 
                      h_old,list_fd,rr,rc):
        

        for i in rr:
            for j in rc[i]:
                pass
    #TODO: Everything :(

        
    def do_next_h_impl(self, surface, subsurface, rain_arr, cumulative,
                  hydrographs, flow_control, courant, potRain, delta_t):

        global infilt_capa
        global max_infilt_capa
        global infilt_time

        rr, rc = GridGlobals.get_region_dim()
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()

       
        