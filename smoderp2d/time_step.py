# @package smoderp2d.time_step methods to performe
#  time step, and to store intermeriate variables

import math
from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt

import copy
import numpy as np


from smoderp2d.core.surface import sheet_runoff
from smoderp2d.core.surface import rill_runoff
from smoderp2d.core.surface import surface_retention
from smoderp2d.core.surface import sheet_to_rill
from smoderp2d.providers import Logger

infilt_capa = 0
infilt_time = 0
max_infilt_capa = 0.00  # [m]


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that if the time step is adjusted
#
class TimeStep:

    def do_sheet_flow(self, surface, subsurface, delta_t, flow_control, courant, courant_rill):

        global infilt_capa
        global max_infilt_capa
        global infilt_time

        rr, rc = GridGlobals.get_region_dim()
        fc = flow_control
        sr = Globals.get_sr()
        itera = Globals.get_itera()
        combinatIndex = Globals.get_combinatIndex()
        NoDataValue = GridGlobals.get_no_data()

        # calculate potential rainfall
        potRain, fc.tz = rain_f.timestepRainfall(
            itera, fc.total_time, delta_t, fc.tz, sr)
        
        for iii in combinatIndex:
            index = iii[0]
            k = iii[1]
            s = iii[2]
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

        # count inactive cell in the computaino domain
        skipped_cell = 0

        for i in rr:
            for j in rc[i]:

                # sheet water level in previous time step

                h_sheet_pre = surface.arr[i][j].h_sheet_pre
                
                skip = (h_sheet_pre == 0.0) and (potRain == 0.0)
                if (skip):
                    sur_bil = h_sheet_pre
                    skipped_cell += 1
                else:
                    # actual rainfall
                    # TODO actual rainfall is still potential rainfall
                    act_rain = potRain
                    # act_rain, fc.sum_interception, rain_arr.arr[i][j].veg_true = rain_f.current_rain(
                    # rain_arr.arr[i][j], potRain, fc.sum_interception)
                    # store current rain
                    surface.arr[i][j].cur_rain = act_rain

                    # sheet inflows
                    inflows = surface.cell_sheet_inflows(i, j, delta_t, courant)
                    
                    # rill in pre
                    inflows_rill = surface.cell_rill_inflows(i, j, delta_t, courant_rill)
                    
                    # sheet outflow
                    outflow = sheet_runoff(i, j, surface.arr[i][j], delta_t, courant)

                    # calculate surface balance
                    sur_bil = h_sheet_pre + act_rain + inflows + inflows_rill - outflow

                    # reduce be infiltration
                    sur_bil, infiltration = infilt.philip_infiltration(
                        surface.arr[i][j].soil_type, sur_bil)

                    # store current infiltration
                    surface.arr[i][j].infiltration = infiltration

                surface.arr[i][j].h_sheet_new = sur_bil

       
        Logger.debug('Highest courant value          {0:.5f}'.format(courant.cour_most))
        Logger.debug('Highest veloviy value          {0:.5f}'.format(courant.cour_speed))
        Logger.debug('i of the highest courant value {}'.format(courant.i))
        Logger.debug('j of the highest courant value {}'.format(courant.j))
        if (not(skipped_cell == 0)):
            Logger.debug('Inactive cells were skipped: {}'.format(skipped_cell))


    def do_rill_flow(self, surface, delta_t, flow_control, courant_rill, N):

        rr, rc = GridGlobals.get_region_dim()
        delta_t_rill = delta_t / N
        
        skipped_cell = 0
        for i in rr:
            for j in rc[i]:
                
                h_rill_pre = surface.arr[i][j].h_rill_pre
                h_sheet_to_rill = surface.arr[i][j].h_sheet_to_rill/N
                
                skip = (h_rill_pre == 0.0) and (h_sheet_to_rill == 0.0)
                if (skip) :
                    rill_bill = 0
                    skipped_cell += 1
                else :
                    
                    # rill out pre
                    outflow = rill_runoff(i, j, surface, delta_t_rill, courant_rill)
                    
                    #courant.CFL(i, j, outflow/delta_t_rill, delta_t_rill)
                    
                    rill_bill = max(h_rill_pre + h_sheet_to_rill - outflow, 0.0)
                    #print h_sheet_to_rill, outflow
                    
                surface.arr[i][j].h_rill_new = rill_bill
                
        Logger.debug('Highest courant value          {0:.5f}'.format(courant_rill.cour_most))
        Logger.debug('Highest veloviy value          {0:.5f}'.format(courant_rill.cour_speed))
        Logger.debug('i of the highest courant value {}'.format(courant_rill.i))
        Logger.debug('j of the highest courant value {}'.format(courant_rill.j))
        if (not(skipped_cell == 0)):
            Logger.debug('Inactive cells were skipped: {}'.format(skipped_cell))
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    