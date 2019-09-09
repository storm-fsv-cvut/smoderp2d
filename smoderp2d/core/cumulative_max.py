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

        self.arrs['exfiltration'] = ('core', 'cExfiltr_m3')
        self.arrs['percolation']  = ('core', 'cPercol_m3')
        self.arrs['h_sub']        = ('core', 'mWLevelSub_M')
        self.arrs['q_sub']        = ('core', 'mQSub_m3_s')
        self.arrs['vol_sub']        = ('core', 'cVOutSub_m3')

        r = self.r
        c = self.c

        # TODO: create arrays with self.arrs.keys() for cycle 
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
        self.vol_sub = np.zeros([r, c], float)

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
        self.arrs = {'infiltration' : ('core', 'cInfil_m3'),       # 1
                     'precipitation': ('core', 'cRain_m3'),        # 2
                     'h_sur_tot'    : ('control', 'mWLevel_m'),    # 3
                     'q_sheet'      : ('control', 'mQsheet_m3_s'), # 4
                     'vol_sheet'    : ('control', 'cSheetVOutM3'), # 5
                     'v_sheet'      : ('control', 'mVel_m_s'),     # 6
                     'shear_sheet'  : ('control', 'mrSearStr_Pa'), # 7
                     'h_rill'       : ('control', 'mWLevelRill_m'),# 8
                     'q_rill'       : ('control', 'mQRill_m3_s'),  # 9
                     'vol_rill'     : ('control', 'cRillVOut_m3'), # 10
                     'b_rill'       : ('control', 'widthRill'),    # 11
                     'inflow_sur'   : ('control', 'cVIn_M3'),      # 12
                     'sur_ret'      : ('control', 'surRet_M'),     # 13
                     'vol_sur_r'    : ('control', 'CumVRestL3'),   # 14 not being used 
                     'q_sur_tot'    : ('core', 'mQsur_m3_s'),      # 15
                     'vol_sur_tot'  : ('core', 'cVsur_m3')         # 16
        }

        # arrays which stores variables defined in self.arrs is defined
        # based on the dictionary keys self.arrs
        for item in self.arrs.keys():
            setattr(self,item,
                    np.zeros([self.r, self.c], float))


    # Method is used after each time step to save the desired variables.
    #
    #  Method is called in smoderp2d.runoff
    #
    def update_cumulative(self, i, j, sur_arr_el, subsur_arr_el, delta_t):
        """ Update arrays with cumulative and maximum 
        values of key computation results.
        
        :param int i:
        :param int j:
        :param float sur_arr_el: single element in surface.arr
        :param float subsur_arr_el: single element in subsurface.arr (to be
        implemented)
        :param floet delta_t: length of time step
        """

        self.infiltration[i][j] += sur_arr_el.infiltration * self.pixel_area
        self.precipitation[i][j] += sur_arr_el.cur_rain * self.pixel_area
        self.vol_sheet[i][j] += sur_arr_el.vol_runoff
        #self.v_sur_r[i][j] += sur_arr_el.vol_rest
        self.vol_sur_tot[i][j] += sur_arr_el.vol_runoff_rill + sur_arr_el.vol_runoff
        self.inflow_sur[i][j] += sur_arr_el.inflow_tm
        self.sur_ret[i][j] += sur_arr_el.cur_sur_ret * self.pixel_area

        q_sheet = sur_arr_el.vol_runoff / delta_t
        q_rill = sur_arr_el.vol_runoff_rill / delta_t
        q_tot = q_sheet + q_rill
        if q_tot > self.q_sur_tot[i][j]:
            self.q_sur_tot[i][j] = q_tot

        if sur_arr_el.state == 0:
            if sur_arr_el.h_total_new > self.h_sur_tot[i][j]:
                self.h_sur_tot[i][j] = sur_arr_el.h_total_new
                self.q_sheet[i][j] = q_sheet

        elif (sur_arr_el.state == 1) or (sur_arr_el.state == 2):
            self.vol_rill[i][j] += sur_arr_el.vol_runoff_rill
            #self.v_rill_r[i][j] += sur_arr_el.v_rill_rest
            if sur_arr_el.h_total_new > self.h_sur_tot[i][j]:
                self.h_sur_tot[i][j] = sur_arr_el.h_total_new
                self.q_sheet[i][j] = q_sheet

            elif sur_arr_el.h_rill > self.h_rill[i][j]:
                self.h_rill[i][j] = sur_arr_el.h_rill
                self.b_rill[i][j] = sur_arr_el.rillWidth
                self.q_rill[i][j] = q_rill

        self.update_cumulative_sur(
            i, j,
            subsur_arr_el,
            subsur_arr_el
        )
