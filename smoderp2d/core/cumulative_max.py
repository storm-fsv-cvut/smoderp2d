# @package smoderp2d.core.cumulative_max
#
#  package contains classes save the cumulative or maximum
#  values of the results in each time step.
#
#

import numpy as np

from smoderp2d.providers import Logger
from smoderp2d.core.general import GridGlobals, Globals


class CumulativeData:
    """TODO."""

    def __init__(self, data_type, file_name):
        """TODO.

        :param data_type: TODO
        :param file_name: TODO
        """
        self.data_type = data_type
        self.file_name = file_name


class CumulativeSubsurfacePass(object):
    """Empty (pass) Class.

    Class is inherited by the class Cumulative if the subsurface flow is not
    desired.
    """

    def __init__(self):
        """TODO."""
        self.data = {}

    def update_cumulative_sur(self, subsurface):
        """TODO.

        :param subsurface: TODO
        """
        pass


class CumulativeSubsurface(CumulativeSubsurfacePass):
    """Max and cumulative values of the subsurface flow.

    Stores arrays of max or cumulative values of important variables of
    the subsurface flow.

    The class is inhered by the class Cumulative
    if the subsurface computation is desired
    """

    def __init__(self):
        """TODO."""
        super(CumulativeSubsurface, self).__init__()

        Logger.info('Subsurface')

        self.data.update({
            # cumulative exfiltration volume [m3]
            'exfiltration': CumulativeData('core', 'cexfiltr_m3'),
            # cumulative percolation volume [m3]
            'percolation' : CumulativeData('core', 'cpercol_m3'),
            # maximum water level in the subsurface soil layer [m]
            'h_sub'       : CumulativeData('core', 'mwlevelsub_m'),
            # maximum subsurface flux [m3s-1]
            'q_sub'       : CumulativeData('core', 'mqsub_m3_s'),
            # cumulative outflow volume in subsurface soil layer [m3]
            'vol_sub'     : CumulativeData('core', 'cvoutsub_m3')
        })

    def update_cumulative_subsur(self, i, j, sub, q_subsur):
        """Save the desired variables.

        Method is used after each time step.

        :param i: TODO
        :param j: TODO
        :param sub: TODO
        :param q_subsur: TODO
        """
        self.exfiltration[i][j] += sub.exfiltration * GridGlobals.pixel_area
        self.percolation[i][j] += sub.percolation * GridGlobals.pixel_area
        self.v_sub[i][j] += sub.vol_runoff

        if sub.h > self.h_sub[i][j]:
            self.h_sub[i][j] = sub.h
        if q_subsur > self.q_sub[i][j]:
            self.q_sub[i][j] = q_subsur


class Cumulative(CumulativeSubsurface if Globals.subflow else CumulativeSubsurfacePass):
    """Max and Cumulative values.

    Stores array of max or cumulative values at of important variables from
    the surface and rill flow.
    """

    def __init__(self):
        """TODO."""
        super(Cumulative, self).__init__()

        Logger.info('Save cumulative and maximum values from: Surface')

        # Dictionary stores the python arrays identification.
        self.data.update({
            # cumulative infiltrated volume [m3]
            'infiltration' : CumulativeData('control', 'cinfil_m3'),
            # cumulative precipitation volume [m3]
            'precipitation': CumulativeData('control', 'crain_m3'),
            # maximum surface water level [m]
            'h_sur_tot'    : CumulativeData('core',    'mwlevel_m'),
            # maximum sheet discharge [m3s-1]
            'q_sheet_tot'  : CumulativeData('control', 'mqsheet_m3_s'),
            # cumulative sheet runoff volume [m3]
            'vol_sheet'    : CumulativeData('control', 'csheetvout_m3'),
            # maximum sheet velocity [ms-1]
            'v_sheet'      : CumulativeData('core',    'mvel_m_s'),
            # maximum sheet shear stress [Pa]
            'shear_sheet'  : CumulativeData('core',    'mrsearstr_pa'),
            # maximum water level in rills [m]
            'h_rill'       : CumulativeData('control',    'mwlevelrill_m'),
            # maximum discharge in rills [m3s-1]
            'q_rill_tot'   : CumulativeData('control', 'mqrill_m3_s'),
            # cumulative runoff volume in rills [m3]
            'vol_rill'     : CumulativeData('control', 'crillvout_m3'),
            # maximum rill width [m]
            'b_rill'       : CumulativeData('control', 'widthrill'),
            # cumulative surface inflow volume [m3]
            'inflow_sur'   : CumulativeData('control', 'cvin_m3'),
            # maximum surface retention [m]
            'sur_ret'      : CumulativeData('control', 'surret_m'),
            # maximum sheet water level [m]
            'h_sheet_tot'  : CumulativeData('control', 'mwlevelsheet_m'),
            # maximal total surface flow [m3/s]
            'q_sur_tot'    : CumulativeData('core',    'mqsur_m3_s'),
            # cumulative total surface flow [m3/s]
            'vol_sur_tot'  : CumulativeData('core',    'cvsur_m3'),
        })

        # step 2b (numpy.ma removal): plain ndarray instead of
        # numpy.ma.masked_array. Validity for output is handled by
        # provider.postprocessing()._make_mask(), which rebuilds the
        # NoData pattern from GridGlobals.rr/rc regardless of array type,
        # so this array no longer needs its own mask.
        for item in self.data.keys():
            setattr(
                self,
                item,
                np.zeros([GridGlobals.r, GridGlobals.c], float)
            )

    def update_cumulative(self, surface, subsurface, delta_t):
        """Update arrays with cumulative and maximum
        values of key computation results.

        :param surface: surface.arr
        :param subsurface: subsurface.arr (to be implemented)
        :param delta_t: current time step length
        """
        # surface.* fields are still numpy.ma arrays until step 2c converts
        # SurArrs. Pull the raw .data explicitly here so every operation
        # below is a plain ndarray operation, regardless of the RHS type -
        # this avoids relying on implicit numpy.ma/ndarray mixed-type
        # dispatch rules.
        surface_infiltration = np.asarray(surface.infiltration)
        surface_cur_rain = np.asarray(surface.cur_rain)
        surface_vol_runoff = np.asarray(surface.vol_runoff)
        surface_vol_runoff_rill = np.asarray(surface.vol_runoff_rill)
        surface_inflow_tm = np.asarray(surface.inflow_tm)
        surface_cur_sur_ret = np.asarray(surface.cur_sur_ret)
        surface_h_total_new = np.asarray(surface.h_total_new)
        surface_h_rill = np.asarray(surface.h_rill)
        surface_rillWidth = np.asarray(surface.rillWidth)
        surface_state = np.asarray(surface.state)
        surface_h_crit = np.asarray(surface.h_crit)

        self.infiltration += surface_infiltration * GridGlobals.pixel_area
        self.precipitation += surface_cur_rain * GridGlobals.pixel_area
        self.vol_sheet += surface_vol_runoff
        self.vol_rill += surface_vol_runoff_rill
        self.vol_sur_tot += surface_vol_runoff_rill + surface_vol_runoff
        self.inflow_sur += surface_inflow_tm
        self.sur_ret += surface_cur_sur_ret * GridGlobals.pixel_area

        q_sheet_tot = surface_vol_runoff / delta_t
        q_rill_tot = surface_vol_runoff_rill / delta_t
        q_sur_tot = q_sheet_tot + q_rill_tot

        self.q_sur_tot = np.maximum(q_sur_tot, self.q_sur_tot)
        self.h_sur_tot = np.maximum(surface_h_total_new, self.h_sur_tot)
        self.q_sheet_tot = np.maximum(q_sheet_tot, self.q_sheet_tot)

        cond_h_rill = surface_h_rill > self.h_rill
        self.h_rill = np.where(cond_h_rill, surface_h_rill, self.h_rill)
        self.b_rill = np.where(cond_h_rill, surface_rillWidth, self.b_rill)
        self.q_rill_tot = np.where(cond_h_rill, q_rill_tot, self.q_rill_tot)

        cond_sur_state0 = surface_state == 0
        self.h_sheet_tot = np.where(
            cond_sur_state0,
            np.maximum(self.h_sheet_tot, surface_h_total_new),
            self.h_sheet_tot
        )
        cond_sur_state1 = surface_state == 1
        cond_sur_state2 = surface_state == 2
        self.h_sheet_tot = np.where(
            np.logical_or(cond_sur_state1, cond_sur_state2),
            surface_h_crit,
            self.h_sheet_tot
        )

        self.update_cumulative_sur(subsurface)

    def calculate_vsheet_sheerstress(self):
        """Compute maximum shear stress and velocity."""
        dx = GridGlobals.get_size()[0]

        self.v_sheet = np.where(
            self.h_sur_tot == 0, 0, self.q_sheet_tot / (self.h_sheet_tot * dx)
        )

        # Globals.mat_slope is still numpy.ma (not part of step 2), read
        # its raw .data explicitly for the same reason as in
        # update_cumulative() above.
        self.shear_sheet = (
            self.h_sheet_tot * 9807 * np.asarray(Globals.mat_slope)
        )

    def return_str_val(self, i, j):
        """Return the cumulative precipitation in mm and cumulative runoff.

        Returns the values at a given cell.

        :param i: TODO
        :param j: TODO
        """
        sw = Globals.slope_width
        return (
            '{:.4e}'.format(self.precipitation[i][j]/GridGlobals.pixel_area),
            '{:.4e}'.format(self.vol_sur_tot[i][j] * sw)
        )
