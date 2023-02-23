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
    def __init__(self, data_type, file_name):
        self.data_type = data_type
        self.file_name = file_name


class CumulativeSubsurfacePass(object):
    """
    Empty (pass) Class

    Class is inherited by the class Cumulative if the subsurface flow is not desired.
    """
    def __init__(self):
        self.data = {}

    def update_cumulative_sur(self, subsurface):
        pass


class CumulativeSubsurface(CumulativeSubsurfacePass):
    """
    Max and cumulative values of the subsurface flow

    Stores arrays of max or cumulative values of important variables of
    the subsurface flow.

    The class is inhered by the class Cumulative
    if the subsurface computation is desired
    """

    def __init__(self):
        super(CumulativeSubsurface, self).__init__()

        Logger.info('Subsurface')

        self.data.update({
            # cumulative exfiltration volume [m3]
            'exfiltration': CumulativeData('core', 'cExfiltr_m3'),     # 1
            # cumulative percolation volume [m3]
            'percolation' : CumulativeData('core', 'cPercol_m3'),      # 2
            # maximum water level in the subsurface soil layer [m]
            'h_sub'       : CumulativeData('core', 'mWLevelSub_M'),    # 3
            # maximum subsurface flux [m3s-1]
            'q_sub'       : CumulativeData('core', 'mQSub_m3_s'),      # 4
            # cumulative outflow volume in subsurface soil layer [m3]
            'vol_sub'     : CumulativeData('core', 'cVOutSub_m3')      # 5
        })

    def update_cumulative_subsur(self, i, j, sub, q_subsur):
        """
        Method is used after each time step to save the desired variables.
        """
        self.exfiltration[i][j] += sub.exfiltration * GridGlobals.pixel_area
        self.percolation[i][j] += sub.percolation * GridGlobals.pixel_area
        self.v_sub[i][j] += sub.vol_runoff

        if sub.h > self.h_sub[i][j]:
            self.h_sub[i][j] = sub.h
        if q_subsur > self.q_sub[i][j]:
            self.q_sub[i][j] = q_subsur


class Cumulative(CumulativeSubsurface if Globals.subflow else CumulativeSubsurfacePass):
    """
    Max and Cumulative values

    Stores array of max or cumulative values at of important variables from
    the surface and rill flow.
    """

    def __init__(self):
        super(Cumulative, self).__init__()

        Logger.info('Save cumulative and maximum values from: Surface')

        # Dictionary stores the python arrays identification.
        self.data.update({
            # cumulative infiltrated volume [m3]
            'infiltration' : CumulativeData('core',    'cInfil_m3'),     # 1
            # cumulative precipitation volume [m3]
            'precipitation': CumulativeData('core',    'cRain_m3'),      # 2
            # maximum surface water level [m]
            'h_sur_tot'    : CumulativeData('control', 'mWLevel_m'),     # 3
            # maximum sheet discharge [m3s-1]
            'q_sheet_tot'  : CumulativeData('control', 'mQsheet_m3_s'),  # 4
            # cumulative sheet runoff volume [m3]
            'vol_sheet'    : CumulativeData('control', 'cSheetVOutM3'),  # 5
            # maximum sheet velocity [ms-1]
            'v_sheet'      : CumulativeData('control', 'mVel_m_s'),      # 6
            # maximum sheet shear stress [Pa]
            'shear_sheet'  : CumulativeData('control', 'mrSearStr_Pa'),  # 7
            # maximum water level in rills [m]
            'h_rill'       : CumulativeData('control', 'mWLevelRill_m'), # 8
            # maximum discharge in rills [m3s-1]
            'q_rill_tot'   : CumulativeData('control', 'mQRill_m3_s'),   # 9
            # cumulative runoff volume in rills [m3]
            'vol_rill'     : CumulativeData('control', 'cRillVOut_m3'),  # 10
            # maximum rill width [m]
            'b_rill'       : CumulativeData('control', 'widthRill'),     # 11
            # cumulative surface inflow volume [m3]
            'inflow_sur'   : CumulativeData('control', 'cVIn_M3'),       # 12
            # maximum surface retention [m]
            'sur_ret'      : CumulativeData('control', 'surRet_M'),      # 13
            # maximum sheet water level [m]
            'h_sheet_tot'  : CumulativeData('control', 'mWLevelsheet_m'),  # 14
            # maximal total surface flow [m3/s]
            'q_sur_tot'    : CumulativeData('core',    'mQsur_m3_s'),    # 15
            # cumulative total surface flow [m3/s]
            'vol_sur_tot'  : CumulativeData('core',    'cVsur_m3'),       # 16
        })
        # define arrays class attributes
        for item in self.data.keys():
            setattr(self,
                    item,
                    np.zeros([GridGlobals.r, GridGlobals.c], float)
            )

    # def update_cumulative(self, i, j, sur_arr_el, subsur_arr_el, delta_t):
    def update_cumulative(self, surface, subsurface, delta_t):
        """Update arrays with cumulative and maximum
        values of key computation results.

        :param float surface: surface.arr
        :param float subsurface: subsurface.arr (to be implemented)
        :param floet delta_t: length of time step
        """
        # originally GridGlobals.pixel_area
        # in TF, not +=
        self.infiltration += surface.infiltration * self.pixel_area
        self.precipitation += surface.cur_rain * self.pixel_area
        # in TF, was vol_sheet +=
        self.vol_sheet += surface.vol_runoff
        # did not exist in TF
        self.vol_rill += surface.vol_runoff_rill
        # not exist in original
        # self.v_sur_r += surface.vol_rest
        # in TF, was += surface.vol_rest
        self.v_sur_tot += surface.vol_runoff_rill + surface.vol_runoff
        self.inflow_sur += surface.inflow_tm
        # originally GridGlobals.pixel_area
        self.sur_ret += surface.cur_sur_ret * self.pixel_area

        # in TF, was q_sheet =
        q_sheet_tot = surface.vol_runoff / delta_t
        # in TF, was q_rill =
        q_rill_tot = surface.vol_runoff_rill / delta_t
        # in TF, was q_tot = q_sheet + q_rill
        q_sur_tot = q_sheet_tot + q_rill_tot
        # in TF, self.q_sur_tot = tf.where(q_tot > self.q_sur_tot,
        self.q_sur_tot = np.where(q_sur_tot > self.q_sur_tot,
                                  q_sur_tot, self.q_sur_tot)
        # new
        self.h_sur_tot = np.wehere(surface.arr.h_total_new > self.h_sur_tot,
                                   surface.arr.h_total_new,
                                   self.h_sur_tot)
        # new
        self.q_sheet_tot = np.where(q_sheet_tot > self.q_sheet_tot,
                                    q_sheet_tot,
                                    self.q_sheet_tot)
        # new
        cond_h_rill = np.greater(surface.h_rill, self.h_rill)
        # new
        self.h_rill = np.where(cond_h_rill, surface.h_rill, self.h_rill)
        # new
        self.b_rill = np.where(cond_h_rill, surface.rillWidth, self.b_rill)
        # new
        self.q_rill_tot = np.where(cond_h_rill, q_rill_tot, self.q_rill_tot)

        # new
        cond_sur_state0 = surface.arr.state == 0
        # in TF, was h_sur instead of h_sheet_tot
        self.h_sheet_tot  = np.where(
            cond_sur_state0,
            np.maximum(self.h_sheet_tot, surface.arr.h_total_new),
            self.h_sheet_tot
        )
        cond_sur_state1 = surface.arr.state == 1
        cond_sur_state2 = surface.arr.state == 2
        self.h_sheet_tot  = np.where(
            cond_sur_state1 | cond_sur_state2,
            surface.h_crit,
            self.h_sheet_tot
        )

#         #####################
#
#         cond = tf.equal(surface.arr.state, 0)
#         cond_in_true = surface.h_total_new > self.h_sur
#         cond_in_false_1 = tf.equal(surface.arr.state, 1)
#         cond_in_false_2 = tf.equal(surface.arr.state, 2)
#         cond_in_false = tf.cast(tf.cast(cond_in_false_1, tf.int8) +
#                                 tf.cast(cond_in_false_2, tf.int8),
#                                 tf.bool)
#         cond_in_false_true = surface.h_total_new > self.h_sur
#         cond_in_false_false = surface.h_rill > self.h_rill
#
#         h_sur_in_true = tf.where(cond_in_true, surface.h_total_new, self.h_sur)
#         h_sur_in_false = tf.where(cond_in_false_true,
#                                   surface.h_total_new, self.h_sur)
#         h_sur_in_false = tf.where(cond_in_false, h_sur_in_false, self.h_sur)
#         self.h_sur = tf.where(cond, h_sur_in_true, h_sur_in_false)
#
#         q_sur_in_true = tf.where(cond_in_true, q_sheet, self.q_sur)
#         q_sur_in_false = tf.where(cond_in_false_true, q_sheet, self.q_sur)
#         q_sur_in_false = tf.where(cond_in_false, q_sur_in_false, self.q_sur)
#         self.q_sur = tf.where(cond, q_sur_in_true, q_sur_in_false)
#
#         self.v_rill = tf.where(cond_in_false, surface.vol_runoff_rill, self.v_rill)
#         self.v_rill_r = tf.where(cond_in_false,
#                                  surface.v_rill_rest, self.v_rill_r)
#
#         q_rill_in_false_false = tf.where(cond_in_false_false,
#                                          q_rill, self.q_rill)
#         q_rill_in_false_true = tf.where(cond_in_false_true,
#                                         self.q_rill, q_rill_in_false_false)
#         q_rill_in_false = tf.where(cond_in_false,
#                                    q_rill_in_false_true, self.q_rill)
#         self.q_rill = tf.where(cond, self.q_rill, q_rill_in_false)
#
#         h_rill_in_false_false = tf.where(cond_in_false_false,
#                                          surface.h_rill, self.h_rill)
#         h_rill_in_false_true = tf.where(cond_in_false_true,
#                                         self.h_rill, h_rill_in_false_false)
#         h_rill_in_false = tf.where(cond_in_false,
#                                    h_rill_in_false_true, self.h_rill)
#         self.h_rill = tf.where(cond, self.h_rill, h_rill_in_false)
#
#         b_rill_in_false_false = tf.where(cond_in_false_false,
#                                          surface.rillWidth, self.b_rill)
#         b_rill_in_false_true = tf.where(cond_in_false_true,
#                                         self.b_rill, b_rill_in_false_false)
#         b_rill_in_false = tf.where(cond_in_false,
#                                    b_rill_in_false_true, self.b_rill)
#         self.b_rill = tf.where(cond, self.b_rill, b_rill_in_false)
#
#         # TODO TF: Really?
#         i = j = 0
# >>>>>>> 095f262 (surface in multiple 2-D arrays instead of one 3-D)
        self.update_cumulative_sur(subsurface)

    def calculate_vsheet_sheerstress(self):
        """Compute maximum shear stress and velocity."""
        rrows = GridGlobals.rr
        rcols = GridGlobals.rc
        dx = GridGlobals.get_size()[0]
        for i in rrows:
            for j in rcols[i]:
                if self.h_sur_tot[i][j] == 0.:
                    self.v_sheet[i][j] = 0.
                else:
                    self.v_sheet[i][j] = \
                        self.q_sheet_tot[i][j] / (self.h_sheet_tot[i][j] * dx)
                self.shear_sheet[i][j] = \
                    self.h_sheet_tot[i][j] * 9807 * Globals.mat_slope[i][j]

    def return_str_val(self, i, j):
        """ returns the cumulative precipitation in mm and cumulative runoff
        at a given cell"""
        sw = Globals.slope_width
        return '{:.4e}'.format(self.precipitation[i][j]/GridGlobals.pixel_area), \
            '{:.4e}'.format(self.vol_sur_tot[i][j] * sw)
