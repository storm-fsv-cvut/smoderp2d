# @package smoderp2d.core.cumulative_max
#
#  package contains classes save the cumulative or maximum
#  values of the results in each time step.
#
#


# globals import
import numpy as np


# smoderp import
from smoderp2d.core.general import *
from smoderp2d.providers import Logger

from smoderp2d.core.general import GridGlobals, Globals


# Max and cumulative values of the subsurface flow
#
#  Stores arrays of max or cumulative values of important variables of
#  the subsurface flow \n
#
#  The class is inhered by the class Cumulative
#  if the subsurface computation is desired
#
#
class CumulativeSubsurface(object):

    # constructor
    #

    def __init__(self):

        Logger.info('Subsurface')
        super(CumulativeSubsurface, self).__init__()

        self.arrs[17] = 'exfiltration'
        self.arrs[18] = 'percolation'
        self.arrs[19] = 'h_sub'
        self.arrs[20] = 'q_sub'
        self.arrs[21] = 'v_sub'

        self.names[17] = 'CumExfiltrL3'
        self.names[18] = 'CumPercolL3'
        self.names[19] = 'MaxWaterSubL'
        self.names[20] = 'MaxQSubL3t_1'
        self.names[21] = 'CumVOutSubL3'

        r = self.r
        c = self.c

        self.n += 5

        # cumulative exfiltration volume [m3]
        self.exfiltration = np.zeros([r, c], float)
        # cumulative percolation volume [m3]
        self.percolation = np.zeros([r, c], float)
        # maximum water level in rills [m]
        #
        #  the height is related to the total cell area not the rill ares
        #
        self.h_sub = np.zeros([r, c], float)
        # maximum discharge from rills [m3s-1]
        self.q_sub = np.zeros([r, c], float)
        # cumulative outflow volume in rills [m3]
        self.v_sub = np.zeros([r, c], float)

    # Method is used after each time step to save the desired variables.
    #
    #  Method is called in smoderp2d.runoff
    #
    def update_cumulative_subsur(self, i, j, sub, q_subsur):

        self.exfiltration[i][j] += sub.exfiltration * self.pixel_area
        self.percolation[i][j] += sub.percolation * self.pixel_area
        self.v_sub[i][j] += sub.vol_runoff

        if sub.h > self.h_sub[i][j]:
            self.h_sub[i][j] = sub.h
        if q_subsur > self.q_sub[i][j]:
            self.q_sub[i][j] = q_subsur


# Empty (pass) Class
#
# Class is inherited by the class Cumulative if the subsurface flow is not desired.
#
class CumulativeSubsurfacePass(object):

    # Method is used after each time step.
    #
    #  Method is called in smoderp2d.runoff
    #

    def update_cumulative_sur(self, i, j, sub, q_subsur):
        pass


# Max and Cumulative values
#
#  Stores array of max or cumulative values at of important variables from
#  the surface and rill flow
#
#
class Cumulative(GridGlobals, CumulativeSubsurface if Globals.subflow else CumulativeSubsurfacePass, Globals, Size):

    # the constructor
    #
    #

    def __init__(self):
        super(GridGlobals, self).__init__()

        Logger.info('Save cumulative and maximum values from: Surface')

        # Dictionary stores the python arrays identification.
        #
        #  self.arr is used in the smoderp2d.io_functions.post_proc
        #
        self.arrs = {1: 'infiltration',
                     2: 'precipitation',
                     3: 'h_sur',
                     4: 'q_sur',
                     5: 'v_sur',
                     6: 'v_sur',
                     7: 'shear_sur',
                     8: 'h_rill',
                     9: 'q_rill',
                     10: 'v_rill',
                     11: 'b_rill',
                     12: 'inflow_sur',
                     13: 'sur_ret',
                     14: 'v_sur_r',
                     15: 'q_sur_tot',
                     16: 'v_sur_tot'
                     }

                # 12 : 'v_rill',

        # Dictionary stores the the arrays name used in the output rasters.
        #
        #  self.names is used in the smoderp2d.io_functions.post_proc
        #
        self.names = {1: 'cinfil_m',
                      2: 'crainf_m',
                      3: 'cVInM3',
                      4: 'MaxQL3t_1',
                      5: 'cSheetVOutM3',
                      6: 'mvel_m_s',
                      7: 'mshearstr_pa',
                      8: 'MaxWaterRillL',
                      9: 'MaxQRillL3t_1',
                      10: 'cRillVOutL3',
                      11: 'AreaRill',
                      12: 'CumVInL3',
                      13: 'SurRet',
                      14: 'CumVRestL3',
                      15: 'msurfl_m3_s',
                      16: 'csurvout_m3_s'
                      }
                # 12 : 'MaxVeloRill',

        # array count stored in the class
        self.n = 13
        # cumulative infiltrated volume [m3]
        self.infiltration = np.zeros([self.r, self.c], float)
        # cumulative precipitation volume [m3]
        self.precipitation = np.zeros([self.r, self.c], float)
        # maximum surface water level [m]
        self.h_sur = np.zeros([self.r, self.c], float)
        # maximum surface discharge [m3s-1]
        self.q_sur = np.zeros([self.r, self.c], float)
        # cumulative surface runoff volume [m3]
        self.v_sur = np.zeros([self.r, self.c], float)
        # cumulative surface runoff volume [m3]
        self.v_sur_r = np.zeros([self.r, self.c], float)
        # maximum surface velocity [ms-1]
        self.v_sur = np.zeros([self.r, self.c], float)
        # maximum surface shear stress [Pa]
        self.shear_sur = np.zeros([self.r, self.c], float)
        # cumulative surface inflow volume [m3]
        self.inflow_sur = np.zeros([self.r, self.c], float)
        # maximum water level in rills [m]
        self.h_rill = np.zeros([self.r, self.c], float)
        # maximum discharge in rills [m3s-1]
        self.q_rill = np.zeros([self.r, self.c], float)
        # cumulative runoff volume in rills [m3]
        self.v_rill = np.zeros([self.r, self.c], float)
        # cumulative runoff volume in rills [m3]
        self.v_rill_r = np.zeros([self.r, self.c], float)
        # maximum rill width [m]
        self.b_rill = np.zeros([self.r, self.c], float)
        # maximum velocity in rills [ms-1]
        self.v_rill = np.zeros([self.r, self.c], float)
        # maximum surface retention [m]
        self.sur_ret = np.zeros([self.r, self.c], float)
        # maximal total surface flow [m3/s]
        self.q_sur_tot = np.zeros([self.r, self.c], float)
        # cumulative total surface flow [m3/s]
        self.v_sur_tot = np.zeros([self.r, self.c], float)

    # Method is used after each time step to save the desired variables.
    #
    #  Method is called in smoderp2d.runoff
    #
    def update_cumulative(self, surface, subsurface, delta_t):

        self.infiltration = surface[:, :, 11] * self.pixel_area
        self.precipitation += surface[:, :, 3] * self.pixel_area
        self.v_sur += surface[:, :, 7]
        self.v_sur_r += surface[:, :, 8]
        self.v_sur_tot += surface[:, :, 8] + surface[:, :, 7]
        self.inflow_sur += surface[:, :, 9]
        self.sur_ret += surface[:, :, 2] * self.pixel_area

        q_sheet = surface[:, :, 7] / delta_t
        q_rill = surface[:, :, 17] / delta_t
        q_tot = q_sheet + q_rill
        self.q_sur_tot = tf.where(q_tot > self.q_sur_tot,
                                  q_tot, self.q_sur_tot)

        cond = tf.equal(surface[:, :, 0], 0)
        cond_in_true = surface[:, :, 5] > self.h_sur
        cond_in_false_1 = tf.equal(surface[:, :, 0], 1)
        cond_in_false_2 = tf.equal(surface[:, :, 0], 2)
        cond_in_false = tf.cast(tf.cast(cond_in_false_1, tf.int8) +
                                tf.cast(cond_in_false_2, tf.int8),
                                tf.bool)
        cond_in_false_true = surface[:, :, 5] > self.h_sur
        cond_in_false_false = surface[:, :, 15] > self.h_rill

        h_sur_in_true = tf.where(cond_in_true, surface[:, :, 5], self.h_sur)
        h_sur_in_false = tf.where(cond_in_false_true,
                                  surface[:, :, 5], self.h_sur)
        h_sur_in_false = tf.where(cond_in_false, h_sur_in_false, self.h_sur)
        self.h_sur = tf.where(cond, h_sur_in_true, h_sur_in_false)

        q_sur_in_true = tf.where(cond_in_true, q_sheet, self.q_sur)
        q_sur_in_false = tf.where(cond_in_false_true, q_sheet, self.q_sur)
        q_sur_in_false = tf.where(cond_in_false, q_sur_in_false, self.q_sur)
        self.q_sur = tf.where(cond, q_sur_in_true, q_sur_in_false)

        self.v_rill = tf.where(cond_in_false, surface[:, :, 17], self.v_rill)
        self.v_rill_r = tf.where(cond_in_false,
                                 surface[:, :, 18], self.v_rill_r)

        q_rill_in_false_false = tf.where(cond_in_false_false,
                                         q_rill, self.q_rill)
        q_rill_in_false_true = tf.where(cond_in_false_true,
                                        self.q_rill, q_rill_in_false_false)
        q_rill_in_false = tf.where(cond_in_false,
                                   q_rill_in_false_true, self.q_rill)
        self.q_rill = tf.where(cond, self.q_rill, q_rill_in_false)

        h_rill_in_false_false = tf.where(cond_in_false_false,
                                         surface[:, :, 15], self.h_rill)
        h_rill_in_false_true = tf.where(cond_in_false_true,
                                        self.h_rill, h_rill_in_false_false)
        h_rill_in_false = tf.where(cond_in_false,
                                   h_rill_in_false_true, self.h_rill)
        self.h_rill = tf.where(cond, self.h_rill, h_rill_in_false)

        b_rill_in_false_false = tf.where(cond_in_false_false,
                                         surface[:, :, 19], self.b_rill)
        b_rill_in_false_true = tf.where(cond_in_false_true,
                                        self.b_rill, b_rill_in_false_false)
        b_rill_in_false = tf.where(cond_in_false,
                                   b_rill_in_false_true, self.b_rill)
        self.b_rill = tf.where(cond, self.b_rill, b_rill_in_false)

        # TODO TF: Really?
        i = j = 0
        self.update_cumulative_sur(
            i,
            j,
            subsurface.arr[i][j],
            subsurface.q_subsurface)
