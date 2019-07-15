"""Package contains classes and methods to compute surface processes.
"""

import numpy as np
import math

from smoderp2d.core.general import Globals, GridGlobals, Size
if Globals.isStream:
    from smoderp2d.core.stream import Stream
else:
    from smoderp2d.core.stream import StreamPass as Stream
from smoderp2d.core.kinematic_diffuse import Kinematic
import smoderp2d.processes.rill as rill
import smoderp2d.processes.surface as surfacefce

from smoderp2d.providers import Logger

courantMax = 1.0
RILL_RATIO = 0.7

class SurArrs(object):
    """Surface attributes."""
    def __init__(self, sur_ret, inf_index, hcrit, a, b):
        """Constructor of Surface array

        Assign values into surface parameters.

        :param sur_ret: TODO
        :inf_index: TODO
        :hcrit: TODO
        :a: TODO
        :b: TODO
        """
        self.state = 0
        self.sur_ret = sur_ret
        self.cur_sur_ret = 0.
        self.cur_rain = 0.
        self.h_sheet = 0.
        self.h_total_new = 0.
        self.h_total_pre = 0.
        self.vol_runoff = 0.
        # self.vol_runoff_pre = float(0)
        self.vol_rest = 0.
        # self.vol_rest_pre =   float(0)
        self.inflow_tm = 0.
        self.soil_type = inf_index
        self.infiltration = 0.
        self.h_crit = hcrit
        self.a = a
        self.b = b
        self.h_rill = 0.
        self.h_rillPre = 0.
        self.vol_runoff_rill = 0.
        # self.vol_runoff_rill_pre= float(0)
        self.v_rill_rest = 0.
        # self.v_rill_rest_pre =  float(0)
        self.rillWidth = 0.
        self.vol_to_rill = 0.
        self.h_last_state1 = 0.


class Surface(GridGlobals, Size, Stream, Kinematic):
    """Contains data and methods to calculate the surface and rill runoff.
    """
    def __init__(self):
        """The constructor

        Make all numpy arrays and establish the inflow procedure based
        on D8 or Multi Flow Direction Algorithm method.
        """
        GridGlobals.__init__(self)

        Logger.info("Surface: ON")

        self.n = 15

        # assign array objects
        for i in range(self.r):
            for j in range(self.c):
                self.arr[i][j] = SurArrs(
                    Globals.get_mat_reten(i, j),
                    Globals.get_mat_inf_index(i, j),
                    Globals.get_mat_hcrit(i, j),
                    Globals.get_mat_aa(i, j),
                    Globals.get_mat_b(i, j)
                )

        Stream.__init__(self)

        Logger.info("\tRill flow: {}".format('ON' if Globals.isRill else 'OFF'))

    def return_str_vals(self, i, j, sep, dt, extra_out):
        """TODO.

        :param i: row index
        :param j: col index
        :param sep: separator
        :param dt: TODO
        :param extra_out: append extra output

        :return: TODO
        """
        arr = self.arr[i][j]

        # Water_level_[m];Flow_[m3/s];v_runoff[m3];v_rest[m3];Infiltration[];surface_retention[l]
        if not extra_out:
            line = '{0}{sep}{1}{sep}{2}'.format(
                arr.h_total_new,
                arr.vol_runoff / dt + arr.vol_runoff_rill / dt,
                arr.vol_runoff + arr.vol_runoff_rill,
                sep=sep
            )
            bil_ = ''
        else:
            line = '{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}{sep}{7}{sep}{8}'.format(
                arr.h_sheet,
                arr.vol_runoff / dt,
                arr.vol_runoff,
                arr.vol_rest,
                arr.infiltration,
                arr.cur_sur_ret,
                arr.state,
                arr.inflow_tm,
                arr.h_total_new,
                sep=sep
            )

            if Globals.isRill:
                line += '{sep}{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}'.format(
                    arr.h_rill,
                    arr.rillWidth,
                    arr.vol_runoff_rill / dt,
                    arr.vol_runoff_rill,
                    arr.v_rill_rest,
                    arr.vol_runoff / dt + arr.vol_runoff_rill / dt,
                    arr.vol_runoff + arr.vol_runoff_rill,
                    sep=sep
                )

            bil_ = arr.h_total_pre * self.pixel_area + \
                   arr.cur_rain * self.pixel_area + \
                   arr.inflow_tm - \
                   (arr.vol_runoff + arr.vol_runoff_rill + \
                    arr.infiltration * self.pixel_area) - \
                    (arr.cur_sur_ret * self.pixel_area) - \
                    arr.h_total_new * self.pixel_area
            # << + arr.vol_rest + arr.v_rill_rest) + (arr.vol_rest_pre + arr.v_rill_rest_pre)

        return line, bil_


def __runoff(i, j, sur, dt, efect_vrst, ratio):
    """Calculates the sheet and rill flow.

    :param i: row index
    :param j: col index
    :param dt: TODO
    :param efect_vrst: TODO
    :param ratio: TODO

    :return: TODO
    """
    h_total_pre = sur.h_total_pre
    h_crit = sur.h_crit
    state = sur.state  # da se tady podivat v jakym jsem casovym kroku a jak se a

    # sur.state               = update_state1(h_total_pre,h_crit,state)
    sur.h_sheet, sur.h_rill, sur.h_rillPre = compute_h_hrill(
        h_total_pre, h_crit, state, sur.rillWidth, sur.h_rillPre)

    q_sheet = sheet_runoff(sur, dt)

    if sur.h_sheet > 0.0:
        v_sheet = q_sheet / sur.h_sheet
    else:
        v_sheet = 0.0

    if sur.state > 0:
        q_rill, v_rill, ratio, rill_courant = rill_runoff(
            i, j, sur, dt, efect_vrst, ratio
        )
    else:
        q_rill, v_rill, ratio, rill_courant = 0, 0, ratio, 0.0

    return q_sheet, v_sheet, q_rill, v_rill, ratio, rill_courant


def __runoff_zero_comp_type(i, j, sur, dt, efect_vrst, ratio):
    """TODO.

    :param i: row index
    :param j: col index
    :param sur: TOD
    :param dt: TODO
    :param efect_vrst: TODO
    :param ratio: TODO

    :return: TODO
    """
    h_total_pre = sur.h_total_pre
    h_crit = sur.h_crit
    state = sur.state


    # sur.state               = update_state1(h_total_pre,h_crit,state)
    sur.h_sheet = sur.h_total_pre

    q_sheet = sheet_runoff(sur, dt)

    if sur.h_sheet > 0.0:
        v_sheet = q_sheet / sur.h_sheet
    else:
        v_sheet = 0.0

    q_rill = 0
    v_rill = 0

    return q_sheet, v_sheet, q_rill, v_rill, ratio, 0.0


def update_state1(ht_1, hcrit, state, rill_width):
    """TODO.

    :param ht_1: TODO
    :param hcrit: TODO
    :param state: TODO (not used)
    :patam rill_width: TODO (not used)

    :return: TODO
    """
    if ht_1 > hcrit:
        if state == 0:
            return 1
    return state


def compute_h_hrill(h_total_pre, h_crit, state, rill_width, h_rill_pre):
    """TODO.

    :param h_total_pre: TODO
    :param h_crit: TODO
    :param state: TODO (not used)
    :patam rill_width: TODO (not used)
    :patam h_rill_pre: TODO (not used)

    :return: TODO
    """
    if state == 0:
        h_sheet = h_total_pre
        h_rill = 0

        return h_sheet, h_rill, 0

    elif state == 1:
        h_sheet = min(h_crit, h_total_pre)
        h_rill = max(h_total_pre - h_crit, 0)
        hRillPre = h_rill

        return h_sheet, h_rill, h_rill_pre

    else: # elif state == 2:
        if h_total_pre > h_rill_pre:
            h_rill = h_rill_pre
            h_sheet = h_total_pre - h_rill_pre
        else:
            h_rill = h_total_pre
            h_sheet = 0

        return h_sheet, h_rill, h_rill_pre

def sheet_runoff(sur, dt):
    """TODO.

    :param sur: TODO
    :param dt: TODO

    :return: TODO
    """
    q_sheet = surfacefce.shallowSurfaceKinematic(sur)
    sur.vol_runoff = dt * q_sheet * GridGlobals.get_size()[0]
    sur.vol_rest = sur.h_sheet * GridGlobals.get_pixel_area() - sur.vol_runoff

    return q_sheet

def rill_runoff(i, j, sur, dt, efect_vrst, ratio):
    """TODO.

    :param i: row index
    :param j: col index
    :param sur: TODO
    :param dt: TODO
    :param efect_vrst: TODO
    :param ratio: TODO

    :return: TODO
    """

    ppp = False

    n = Globals.get_mat_n(i, j)
    slope = Globals.get_mat_slope(i, j)

    vol_to_rill = sur.h_rill * GridGlobals.get_pixel_area()
    h, b = rill.update_hb(
        vol_to_rill, RILL_RATIO, efect_vrst, sur.rillWidth, ratio, ppp
    )
    r_rill = (h * b) / (b + 2 * h)

    v_rill = math.pow(r_rill, (2.0 / 3.0)) * \
        1. / n * math.pow(slope / 100, 0.5)

    q_rill = v_rill * h * b

    vol_rill = q_rill * dt

    # original based on speed
    courant = (v_rill * dt) / efect_vrst

    # celerita
    # courant = (1 + s*b/(3*(b+2*h))) * q_rill/(b*h)

    sur.vol_to_rill = vol_to_rill
    sur.rillWidth = b
    if courant <= courantMax:
        if vol_rill > vol_to_rill:
            sur.v_rill_rest = 0
            sur.vol_runoff_rill = vol_to_rill
        else:
            sur.v_rill_rest = vol_to_rill - vol_rill
            sur.vol_runoff_rill = vol_rill

    else:
        return q_rill, v_rill, ratio, courant

    return q_rill, v_rill, ratio, courant


def surface_retention(bil, sur):
    """TODO.

    :param bil: TODO
    param sur: TODO
    """
    reten = sur.sur_ret
    pre_reten = reten
    if reten < 0:
        tempBIL = bil + reten

        if tempBIL > 0:
            bil = tempBIL
            reten = 0
        else:
            reten = tempBIL
            bil = 0

    sur.sur_ret = reten
    sur.cur_sur_ret = reten - pre_reten

    return bil

if Globals.isRill:
    runoff = __runoff
else:
    runoff = __runoff_zero_comp_type
