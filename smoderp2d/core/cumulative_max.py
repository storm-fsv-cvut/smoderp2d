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

        self.arrs['exfiltration'] = ('core', 'CumExfiltrL3')
        self.arrs['percolation']  = ('core', 'CumPercolL3')
        self.arrs['h_sub']        = ('core', 'MaxWaterSubL')
        self.arrs['q_sub']        = ('core', 'MaxQSubL3t_1')
        self.arrs['v_sub']        = ('core', 'CumVOutSubL3')

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

        self.arrs = {'infiltration' : ('core', 'cinfil_m'),
                     'precipitation': ('core', 'crainf_m'),
                     'h_sur'        : ('core', 'cVInM3'),
                     'q_sur'        : ('core', 'MaxQL3t_1'),
                     'v_sur'        : ('core', 'cSheetVOutM3'),
                     'v_sur2'       : ('core', 'mvel_m_s'),
                     'shear_sur'    : ('core', 'mshearstr_pa'),
                     'h_rill'       : ('core', 'MaxWaterRillL'),
                     'q_rill'       : ('core', 'MaxQRillL3t_1'),
                     'v_rill'       : ('core', 'cRillVOutL3'),
                     'b_rill'       : ('core', 'AreaRill'),
                     'inflow_sur'   : ('core', 'CumVInL3'),
                     'sur_ret'      : ('core', 'SurRet'),
                     'v_sur_r'      : ('core', 'CumVRestL3'),
                     'q_sur_tot'    : ('core', 'msurfl_m3_s'),
                     'v_sur_tot'    : ('core', 'csurvout_m3_s')}

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
    def update_cumulative(self, i, j, surface, subsurface, delta_t):

        self.infiltration[i][j] += surface.infiltration * self.pixel_area
        self.precipitation[i][j] += surface.cur_rain * self.pixel_area
        self.v_sur[i][j] += surface.vol_runoff
        self.v_sur_r[i][j] += surface.vol_rest
        self.v_sur_tot[i][j] += surface.vol_rest + surface.vol_runoff
        self.inflow_sur[i][j] += surface.inflow_tm
        self.sur_ret[i][j] += surface.cur_sur_ret * self.pixel_area

        q_sheet = surface.vol_runoff / delta_t
        q_rill = surface.vol_runoff_rill / delta_t
        q_tot = q_sheet + q_rill
        if q_tot > self.q_sur_tot[i][j]:
            self.q_sur_tot[i][j] = q_tot

        if surface.state == 0:
            if surface.h_total_new > self.h_sur[i][j]:
                self.h_sur[i][j] = surface.h_total_new
                self.q_sur[i][j] = q_sheet

        elif (surface.state == 1) or (surface.state == 2):
            self.v_rill[i][j] += surface.vol_runoff_rill
            self.v_rill_r[i][j] += surface.v_rill_rest
            if surface.h_total_new > self.h_sur[i][j]:
                self.h_sur[i][j] = surface.h_total_new
                self.q_sur[i][j] = q_sheet

            elif surface.h_rill > self.h_rill[i][j]:
                self.h_rill[i][j] = surface.h_rill
                self.b_rill[i][j] = surface.rillWidth
                self.q_rill[i][j] = q_rill

        self.update_cumulative_sur(
            i,
            j,
            subsurface.arr[i][j],
            subsurface.q_subsurface)
