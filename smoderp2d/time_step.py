# @package smoderp2d.time_step methods to perform
#  time step, and to store intermediate variables

from smoderp2d.core.general import Globals, GridGlobals
import smoderp2d.processes.rainfall as rain_f
import smoderp2d.processes.infiltration as infilt

import numpy as np
import numpy.ma as ma


from smoderp2d.core.surface import runoff
from smoderp2d.core.surface import surface_retention


# Class manages the one time step operation
#
#  the class also contains methods to store the important arrays to reload that
#  if the time step is adjusted
#
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
        :param delta_t: TODO
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

        runoff_return = runoff(
            surface.arr, delta_t, mat_effect_cont, fc.ratio
        )

        cond_state_flow = surface_state > Globals.streams_flow_inc
        v_sheet = ma.where(cond_state_flow, 0, runoff_return[0])
        v_rill = ma.where(cond_state_flow, 0, runoff_return[1])
        if ma.all(cond_state_flow):
            subsurface.runoff(
                delta_t, mat_effect_cont
            )
        if ma.any(cond_state_flow):
            fc.ratio = ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)),
                mask=GridGlobals.masks
            )
        else:
            # TODO: Better way to make it just a number
            fc.ratio = runoff_return[2]
        rill_courant = ma.where(cond_state_flow, 0, runoff_return[3])
        surface.arr.h_sheet = ma.where(
            cond_state_flow, surface.arr.h_sheet, runoff_return[4]
        )
        surface.arr.h_rill = ma.where(
            cond_state_flow, surface.arr.h_rill, runoff_return[5]
        )
        surface.arr.h_rillPre = ma.where(
            cond_state_flow, surface.arr.h_rillPre, runoff_return[6]
        )
        surface.arr.vol_runoff = ma.where(
            cond_state_flow, surface.arr.vol_runoff, runoff_return[7]
        )
        surface.arr.vol_rest = ma.where(
            cond_state_flow, surface.arr.vol_rest, runoff_return[8]
        )
        surface.arr.v_rill_rest = ma.where(
            cond_state_flow, surface.arr.v_rill_rest, runoff_return[9]
        )
        surface.arr.vol_runoff_rill = ma.where(
            cond_state_flow, surface.arr.vol_runoff_rill, runoff_return[10]
        )
        surface.arr.vel_rill = ma.where(
            cond_state_flow, surface.arr.vel_rill, runoff_return[11]
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

    # self,surface, subsurface, rain_arr, cumulative, hydrographs, potRain,
    # courant, total_time, delta_t, combinatIndex, NoDataValue,
    # sum_interception, mat_effect_cont, ratio, iter_

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
        :param delta_t: TODO
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
                cumulative,
                actRain)
            return actRain

        for iii in combinatIndex:
            k = iii[1]
            s = iii[2]
            # jj * 100.0 !!! smazat
            iii[3] = infilt.phlilip(
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

        #
        # Surface BILANCE
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

        # subsurface inflow
        """
        inflow_sub = subsurface.cell_runoff(i,j,False)
        subsurface.bilance(infiltration,inflow_sub/pixel_area,delta_t)
        subsurface.fill_slope()
        """

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
            cumulative,
            actRain)

        return actRain
