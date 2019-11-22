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

    def update_cumulative_sur(self, i, j, sub, q_subsur):
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
            'q_sheet'      : CumulativeData('control', 'mQsheet_m3_s'),  # 4
            # cumulative sheet runoff volume [m3]
            'vol_sheet'    : CumulativeData('control', 'cSheetVOutM3'),  # 5
            # maximum sheet velocity [ms-1]
            'v_sheet'      : CumulativeData('control', 'mVel_m_s'),      # 6
            # maximum sheet shear stress [Pa]
            'shear_sheet'  : CumulativeData('control', 'mrSearStr_Pa'),  # 7
            # maximum water level in rills [m]
            'h_rill'       : CumulativeData('control', 'mWLevelRill_m'), # 8
            # maximum discharge in rills [m3s-1]
            'q_rill'       : CumulativeData('control', 'mQRill_m3_s'),   # 9
            # cumulative runoff volume in rills [m3]
            'vol_rill'     : CumulativeData('control', 'cRillVOut_m3'),  # 10
            # maximum rill width [m]
            'b_rill'       : CumulativeData('control', 'widthRill'),     # 11
            # cumulative surface inflow volume [m3]
            'inflow_sur'   : CumulativeData('control', 'cVIn_M3'),       # 12
            # maximum surface retention [m]
            'sur_ret'      : CumulativeData('control', 'surRet_M'),      # 13
            # cumulative surface runoff volume [m3]
            'vol_sur_r'    : CumulativeData('control', 'CumVRestL3'),    # 14
            # maximal total surface flow [m3/s]
            'q_sur_tot'    : CumulativeData('core',    'mQsur_m3_s'),    # 15
            # cumulative total surface flow [m3/s]
            'vol_sur_tot'  : CumulativeData('core',    'cVsur_m3')       # 16
        })
        # define arrays class attributes
        for item in self.data.keys():
            setattr(self,
                    item,
                    np.zeros([GridGlobals.r, GridGlobals.c], float)
            )

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
        self.infiltration[i][j] += sur_arr_el.infiltration * GridGlobals.pixel_area
        self.precipitation[i][j] += sur_arr_el.cur_rain * GridGlobals.pixel_area
        self.vol_sheet[i][j] += sur_arr_el.vol_runoff
        self.vol_rill[i][j] += sur_arr_el.vol_runoff_rill
        #self.v_sur_r[i][j] += sur_arr_el.vol_rest
        self.vol_sur_tot[i][j] += sur_arr_el.vol_runoff_rill + sur_arr_el.vol_runoff
        self.inflow_sur[i][j] += sur_arr_el.inflow_tm
        self.sur_ret[i][j] += sur_arr_el.cur_sur_ret * GridGlobals.pixel_area

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
