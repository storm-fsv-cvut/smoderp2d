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

# from smoerp2d.core.surface import sheet_runoff
from smoderp2d.core.surface import sheet_runoff

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.000  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:
    " The function do_flow will be probably not used for implicit method."
    # def do_flow(self, surface, subsurface, delta_t, flow_control, courant):
    #     rr, rc = GridGlobals.get_region_dim()
    #     mat_efect_cont = Globals.get_mat_efect_cont()
    #     fc = flow_control
    #     sr = Globals.get_sr()
    #     itera = Globals.get_itera()

    #     potRain, fc.tz = rain_f.timestepRainfall(
    #         itera, fc.total_time, delta_t, fc.tz, sr
    #     )

    #     for i in rr:
    #         for j in rc[i]:
    #             # TODO: variable not used. Should we delete it?
    #             h_total_pre = surface.arr.get_item([i, j]).h_total_pre

    #             surface_state = surface.arr.get_item([i, j]).state

    #             if surface_state > Globals.streams_flow_inc:
    #                 q_sheet = 0.0
    #                 v_sheet = 0.0
    #                 q_rill = 0.0
    #                 v_rill = 0.0
    #                 rill_courant = 0.0
    #             else:
    #                 q_sheet, v_sheet, q_rill, v_rill, fc.ratio, rill_courant = runoff(
    #                     i, j, surface.arr.get_item([i, j]), delta_t, mat_efect_cont[i][j], fc.ratio
    #                 )
    #                 subsurface.runoff(i, j, delta_t, mat_efect_cont[i][j])

    #             # TODO: variable not used. Should we delete it?
    #             q_surface = q_sheet + q_rill
    #             v = max(v_sheet, v_rill)
    #             co = 'sheet'
    #             courant.CFL(
    #                 i,
    #                 j,
    #                 surface.arr.get_item([i, j]).h_total_pre,
    #                 v,
    #                 delta_t,
    #                 mat_efect_cont[i][j],
    #                 co,
    #                 rill_courant)
    #             # TODO: variable not used. Should we delet it?
    #             rill_courant = 0.

    #             # w1 = surface.arr.get_item([i, j]).vol_runoff_rill
    #             # w2 = surface.arr.get_item([i, j]).v_rill_rest

    #     return potRain


    



    # objective function  
    def model( h_new, dt,h_old,list_fd,r,c,a,b,act_rain,infilt):

        #calculating sheet runoff from all cells
        sheet_flow = np.zeros((r*c))
        for i in range(r):
            for j in range(c):
               sheet_flow [j+i*c] = sheet_runoff (dt,a,b,h_new[j+i*c])
        
        # setting all residuals to zero
        res = np.zeros((r*c))

        # calculating residual for each cell
        for i in range(r):
            for j in range(c):
                # acumulation 
                res[j+i*c] += - (h_new[j+i*c] - h_old[j+i*c])/dt
                # rain and infiltration
                res[j+i*c] += act_rain(i,j) - infilt
                # sheet runoff
                res[j+i*c] += - sheet_flow[j+i*c]
                # sheet inflows from neigbouring cells (try is used to avoid out of range errors)
                try:
                    res[j+i*c] +=  list_fd[j+i*c][0]*sheet_flow[(i-1)*c+j+1] #NE
                except:
                    pass   
                try:
                    res[j+i*c] +=  list_fd[j+i*c][1]*sheet_flow[(i-1)*c+j] #N
                except:
                    pass 
                try:
                    res[j+i*c] +=  list_fd[j+i*c][2]*sheet_flow[(i-1)*c+j-1] #NW
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][3]*sheet_flow[(i)*c+j-1] #W
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][4]*sheet_flow[(i+1)*c+j-1] #SW
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][5]*sheet_flow[(i+1)*c+j] #S
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][6]*sheet_flow[(i+1)*c+j+1] #SE
                except:
                    pass
                try:
                    res[j+i*c] +=  list_fd[j+i*c][7]*sheet_flow[(i)*c+j+1] #E
                except:
                    pass
        return res

    # Method to performe one time step
    def do_next_h(self, surface,  rain_arr, cumulative, 
                  hydrographs, flow_control,  potRain, delta_t,list_fd):

        global infilt_capa
        global max_infilt_capa
        global infilt_time

        r, c = GridGlobals.r, GridGlobals.c
        pixel_area = GridGlobals.get_pixel_area()
        fc = flow_control
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()


        
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
        
        infilt = iii[3].tolist(0)    
        h_old = surface.arr.h_total_pre.ravel()
        h_new0 = h_old


        res = self.model(h_new0, delta_t,h_old,list_fd,r,c,Globals.get_mat_aa(),Globals.get_mat_b(),act_rain,infilt)
        
        return res
        # surface.arr.h_total_pre = h_new
                    