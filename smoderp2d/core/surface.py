"""Package contains classes and methods to compute surface processes.
"""

import numpy as np
import math

from smoderp2d.core.general import Globals, GridGlobals
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
        self.state = np.zeros((GridGlobals.r, GridGlobals.c))
        self.sur_rate = np.ones((GridGlobals.r, GridGlobals.c)) * sur_ret
        self.cur_sur_ret = np.zeros((GridGlobals.r, GridGlobals.c))
        self.cur_rain = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_sheet = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_total_new = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_total_pre = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_runoff = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_rest = np.zeros((GridGlobals.r, GridGlobals.c))
        self.inflow_tm = np.zeros((GridGlobals.r, GridGlobals.c))
        # in TF, Globals.get_mat_inf_index_tf()
        self.soil_type = np.ones((GridGlobals.r, GridGlobals.c)) * inf_index
        self.infiltration = np.zeros((GridGlobals.r, GridGlobals.c))
        # in TF, Globals.get_mat_hcrit_tf()
        self.h_crit = np.ones((GridGlobals.r, GridGlobals.c)) * hcrit
        # in TF, a = Globals.get_mat_aa_tf()
        self.a = np.ones((GridGlobals.r, GridGlobals.c)) * a
        # in TF, Globals.get_mat_b_tf()
        self.b = np.ones((GridGlobals.r, GridGlobals.c)) * b
        self.h_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_rillPre = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_runoff_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vel_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.v_rill_rest = np.zeros((GridGlobals.r, GridGlobals.c))
        self.rillWidth = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_to_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_last_state1 = np.zeros((GridGlobals.r, GridGlobals.c))


# in TF, class Surface(GridGlobals, Size, Stream, Kinematic, SurArrs):
class Surface(GridGlobals, Stream, Kinematic):
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

        # set array outsides to zeros
        self.arr.set_outsides(SurArrs)

        # assign array objects
        self.arr = SurArrs(
            Globals.get_mat_reten_np(),
            Globals.get_mat_inf_index_np(),
            Globals.get_mat_hcrit_np(),
            Globals.get_mat_aa_np(),
            Globals.get_mat_b_np()
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
        arr = self.arr.get_item([i, j])
        sw = Globals.slope_width

        # Water_level_[m];Flow_[m3/s];v_runoff[m3];v_rest[m3];Infiltration[];surface_retention[l]
        if not extra_out:
            line = '{0:.4e}{sep}{1:.4e}'.format(
                arr.h_total_new[i, j],
                (arr.vol_runoff[i, j] / dt + arr.vol_runoff_rill[i, j] / dt) * sw,
                sep=sep
            )
            bil_ = ''
        else:
            velocity = np.where(
                arr.h_sheet == 0,
                0,
                arr.vol_runoff / dt / (arr.h_sheet*GridGlobals.dx)
            )
            # if profile1d provider - the data in extra output are the unit width data
            #                     if you need runoff from non-unit slope and
            #                     with extra output calculate it yourself
            line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3:.4e}{sep}{4:.4e}{sep}'\
            '{5:.4e}{sep}{6:.4e}{sep}{7:.4e}{sep}{8:.4e}{sep}{9:.4e}'.format(
                arr.h_sheet[i, j],
                arr.vol_runoff[i, j] / dt,
                arr.vol_runoff[i, j],
                velocity[i, j],
                arr.vol_rest[i, j],
                arr.infiltration[i, j],
                arr.cur_sur_ret[i, j],
                arr.state[i, j],
                arr.inflow_tm[i, j],
                arr.h_total_new[i, j],
                sep=sep
            )

            if Globals.isRill:
                line += '{sep}{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3:.4e}{sep}{4:.4e}'\
                '{sep}{5:.4e}{sep}{6:.4e}{sep}{7:.4e}'.format(
                    arr.h_rill[i, j],
                    arr.rillWidth[i, j],
                    arr.vol_runoff_rill[i, j] / dt,
                    arr.vol_runoff_rill[i, j],
                    arr.vel_rill[i, j],
                    arr.v_rill_rest[i, j],
                    arr.vol_runoff[i, j] / dt + arr.vol_runoff_rill[i, j] / dt,
                    arr.vol_runoff[i, j] + arr.vol_runoff_rill[i, j],
                    sep=sep
                )

            bil_ = arr.h_total_pre[i, j] * self.pixel_area + \
                   arr.cur_rain[i, j] * self.pixel_area + \
                   arr.inflow_tm[i, j] - \
                   (arr.vol_runoff[i, j] + arr.vol_runoff_rill[i, j] + \
                    arr.infiltration[i, j] * self.pixel_area) - \
                    (arr.cur_sur_ret[i, j] * self.pixel_area) - \
                    arr.h_total_new[i, j] * self.pixel_area
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
    # in TF, rillWidth not passed to the function
    sur.h_sheet, sur.h_rill, sur.h_rillPre = compute_h_hrill(
        h_total_pre, h_crit, state, sur.rillWidth, sur.h_rillPre)

    q_sheet, sur.vol_runoff, sur.vol_rest = sheet_runoff(sur, dt)

    v_sheet = np.where(sur.h_sheet > 0, q_sheet / sur.h_sheet, 0)

    rill_runoff_results = np.where(
        sur.state > 0,
        rill_runoff(i, j, sur, dt, efect_vrst, ratio),
        (0, 0, sur.v_rill_rest, sur.vol_runoff_rill, ratio, 0)
    )
    q_rill, v_rill, sur.v_rill_rest, sur.vol_runoff_rill, ratio, rill_courant = rill_runoff_results

    sur.vel_rill = v_rill
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
    h_sheet = np.where(
        state == 0,
        h_total_pre,
        np.where(
            state == 1,
            np.minimum(h_crit, h_total_pre),
            np.where(h_total_pre > h_rill_pre, h_total_pre - h_rill_pre, 0)
        )
    )
    h_rill = np.where(
        state == 0,
        0,
        np.where(
            state == 1,
            np.maximum(h_total_pre - h_crit, 0),
            np.where(h_total_pre > h_rill_pre, h_rill_pre, h_total_pre)
        )
    )
    h_rill_pre = np.where(
        state == 0,
        0,
        np.where(
            state == 1,
            h_rill,
            h_rill_pre
        )
    )

    if state == 0:
        h_sheet = h_total_pre
        h_rill = 0

        return h_sheet, h_rill, 0

    elif state == 1:
        h_sheet = min(h_crit, h_total_pre)
        h_rill = max(h_total_pre - h_crit, 0)
        h_rill_pre = h_rill

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
    vol_runoff = dt * q_sheet * GridGlobals.get_size()[0]
    # in TF, was h_sheet * GridGlobals.get_pixel_area() - sur.vol_runoff
    vol_rest = sur.h_sheet * GridGlobals.get_pixel_area() - vol_runoff

    return q_sheet, vol_runoff, vol_rest

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

    v_rill = np.power(r_rill, (2.0 / 3.0)) * 1. / n * np.power(slope, 0.5)

    q_rill = v_rill * h * b

    vol_rill = q_rill * dt

    # original based on speed
    courant = (v_rill * dt) / efect_vrst

    # celerita
    # courant = (1 + s*b/(3*(b+2*h))) * q_rill/(b*h)

    sur.vol_to_rill = vol_to_rill
    sur.rillWidth = b
    v_rill_rest = np.where(
        courant <= courantMax,
        np.where(vol_rill > vol_to_rill, 0, vol_to_rill - vol_rill),
        sur.v_rill_rest
    )
    vol_runoff_rill = np.where(
        courant <= courantMax,
        np.where(vol_rill > vol_to_rill, vol_to_rill, vol_rill),
        sur.vol_runoff_rill
    )

    return q_rill, v_rill, v_rill_rest, vol_runoff_rill, ratio, courant


def surface_retention(bil, sur):
    """TODO.

    :param bil: TODO
    param sur: TODO
    """
    reten = sur.sur_ret
    pre_reten = reten
    bil = np.where(
        reten < 0,
        np.where(bil + reten > 0, bil + reten, 0),
        bil
    )
    reten = np.where(
        reten < 0,
        np.where(bil + reten > 0, 0, bil + reten),
        reten
    )

    sur.sur_ret = reten
    sur.cur_sur_ret = reten - pre_reten

    return bil

if Globals.isRill:
    runoff = __runoff
else:
    runoff = __runoff_zero_comp_type
