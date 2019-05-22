"""Package contains classes and methods to compute surface processes.
"""

import numpy as np
import math
import tensorflow as tf

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

    state = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    sur_ret = Globals.get_mat_reten_tf()
    cur_sur_ret = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    cur_rain = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_sheet = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_total_new = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_total_pre = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    vol_runoff = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    vol_rest = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    inflow_tm = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    soil_type = Globals.get_mat_inf_index_tf()
    infiltration = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_crit = Globals.get_mat_hcrit_tf()
    a = Globals.get_mat_aa_tf()
    b = Globals.get_mat_b_tf()
    h_rill = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_rillPre = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    vol_runoff_rill = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    v_rill_rest = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    rillWidth = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    v_to_rill = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)
    h_last_state1 = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float64)

    # def __init__(self, sur_ret, inf_index, hcrit, a, b):
    #     """Constructor of Surface array
    #
    #     Assign values into surface parameters.
    #
    #     :param sur_ret: TODO
    #     :inf_index: TODO
    #     :hcrit: TODO
    #     :a: TODO
    #     :b: TODO
    #     """
    #     self.state = 0
    #     self.sur_ret = sur_ret
    #     self.cur_sur_ret = 0.
    #     self.cur_rain = 0.
    #     self.h_sheet = 0.
    #     self.h_total_new = 0.               # #5
    #     self.h_total_pre = 0.
    #     self.vol_runoff = 0.
    #     # self.vol_runoff_pre = float(0)
    #     self.vol_rest = 0.
    #     # self.vol_rest_pre =   float(0)
    #     self.inflow_tm = 0.                 # #9
    #     self.soil_type = inf_index
    #     self.infiltration = 0.
    #     self.h_crit = hcrit                 # #12
    #     self.a = a
    #     self.b = b
    #     self.h_rill = 0.
    #     self.h_rillPre = 0.
    #     self.vol_runoff_rill = 0.           # #17
    #     # self.vol_runoff_rill_pre= float(0)
    #     self.v_rill_rest = 0.
    #     # self.v_rill_rest_pre =  float(0)
    #     self.rillWidth = 0.
    #     self.v_to_rill = 0.                 # #20
    #     self.h_last_state1 = 0.
    #     # vol_runoff_pre #22
    #     # veg_true                          # #23
    #     # veg
    #     # ppl
    #     # pi #26


class Surface(GridGlobals, Size, Stream, Kinematic, SurArrs):
    """Contains data and methods to calculate the surface and rill runoff.
    """
    def __init__(self):
        """The constructor

        Make all numpy arrays and establish the inflow procedure based
        on D8 or Multi Flow Direction Algorithm method.
        """
        self.dims = 0
        GridGlobals.__init__(self)

        Logger.info("Surface: ON")

        self.n = 15

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
                self.h_total_new[i, j],
                self.vol_runoff[i, j] / dt + self.vol_runoff_rill[i, j] / dt,
                self.vol_runoff[i, j] + self.vol_runoff_rill[i, j],
                sep=sep
            )
            bil_ = ''
        else:
            line = '{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}{sep}{7}{sep}{8}'.format(
                self.h_sheet[i, j],
                self.vol_runoff[i, j] / dt,
                self.vol_runoff[i, j],
                self.vol_rest[i, j],
                self.infiltration[i, j],
                self.cur_sur_ret[i, j],
                self.state[i, j],
                self.inflow_tm[i, j],
                self.h_total_new[i, j],
                sep=sep
            )

            if Globals.isRill:
                line += '{sep}{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}'.format(
                    self.h_rill[i, j],
                    self.rillWidth[i, j],
                    self.vol_runoff_rill[i, j] / dt,
                    self.vol_runoff_rill[i, j],
                    self.v_rill_rest[i, j],
                    self.vol_runoff[i, j] / dt + self.vol_runoff_rill[i, j] / dt,
                    self.vol_runoff[i, j] + self.vol_runoff_rill[i, j],
                    sep=sep
                )

            bil_ = self.h_total_pre[i, j] * self.pixel_area + \
                   self.cur_rain * self.pixel_area + \
                   self.inflow_tm[i, j] - \
                   (self.vol_runoff[i, j] + self.vol_runoff_rill[i, j] + \
                    self.infiltration[i, j] * self.pixel_area) - \
                    (self.cur_sur_ret[i, j] * self.pixel_area) - \
                    self.h_total_new[i, j] * self.pixel_area
            # << + arr.vol_rest + arr.v_rill_rest) + (arr.vol_rest_pre + arr.v_rill_rest_pre)

        return line, bil_


def __runoff(sur, dt, mat_efect_cont, zeros):
    """Calculates the sheet and rill flow.

    :param i: row index
    :param j: col index
    :param dt: TODO
    :param efect_vrst: TODO

    :return: TODO
    """

    sur.h_sheet, sur.h_rill, sur.h_rillPre = compute_h_hrill(
        sur.h_total_pre, sur.h_crit, sur.state,
        sur.h_rillPre, zeros)

    q_sheet, sur.vol_runoff, sur.vol_rest = sheet_runoff(sur, dt, sur.h_sheet)

    v_sheet = tf.where(sur.h_sheet > 0.0, q_sheet / sur.h_sheet, zeros)

    v_rill, rill_courant, v_rill_rest, sur.vol_runoff_rill, sur.rillWidth, sur.v_to_rill \
        = rill_runoff(sur, dt, mat_efect_cont, sur.h_rill, zeros)

    return sur.h_sheet, sur.h_rill, sur.h_rillPre, v_sheet, v_rill, rill_courant, \
           v_rill_rest, sur.vol_runoff_rill, sur.vol_runoff, sur.vol_rest, sur.rillWidth, \
           sur.v_to_rill


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


def compute_h_hrill(h_total_pre, h_crit, state, h_rill_pre, zeros):
    """TODO.

    :param h_total_pre: TODO
    :param h_crit: TODO
    :param state: TODO (not used)
    :patam rill_width: TODO (not used)
    :patam h_rill_pre: TODO (not used)

    :return: TODO
    """
    cond1 = h_total_pre > h_rill_pre
    cond2 = tf.equal(state, 1)
    cond3 = tf.equal(state, 0)

    a = tf.where(cond1,
                 h_total_pre - h_rill_pre,
                 zeros, name='a')
    cond_in_compute_h_hrill = tf.where(
        cond2,
        tf.minimum(h_crit, h_total_pre),
        a, name='cond_in')
    h_sheet = tf.where(cond3, h_total_pre,
                       cond_in_compute_h_hrill)  # SUR4

    a = tf.where(cond1, h_rill_pre, h_total_pre,
                 name='a')
    cond_in_compute_h_hrill = tf.where(
        cond2,
        tf.maximum(h_total_pre - h_crit, zeros),
        a, name='cond_in')
    h_rill = tf.where(cond3, zeros, cond_in_compute_h_hrill)  # SUR15

    a = tf.where(cond1, h_rill_pre, h_rill_pre,
                 name='a')
    cond_in_compute_h_hrill = tf.where(
        cond2,
        h_rill_pre,
        a, name='cond_in')
    h_rillPre = tf.where(cond3, zeros, cond_in_compute_h_hrill)  # SUR16

    return h_sheet, h_rill, h_rillPre

def sheet_runoff(sur, dt, h_sheet):
    """TODO.

    :param sur: TODO
    :param dt: TODO

    :return: TODO
    """
    q_sheet = surfacefce.shallowSurfaceKinematic(
        sur.a, sur.b, h_sheet)
    # TODO: Do I really need to recast?
    q_sheet = tf.dtypes.cast(q_sheet, tf.float64)
    sur.vol_runoff = dt * q_sheet * GridGlobals.get_size()[0]
    sur.vol_rest = h_sheet * GridGlobals.get_pixel_area() - sur.vol_runoff  # SUR7

    return q_sheet, sur.vol_runoff, sur.vol_rest

def rill_runoff(sur, dt, mat_efect_cont, h_rill, zeros):
    """TODO.

    :param i: row index
    :param j: col index
    :param sur: TODO
    :param dt: TODO
    :param efect_vrst: TODO
    :param ratio: TODO

    :return: TODO
    """
    n = Globals.get_mat_n_tf()
    slope = Globals.get_mat_slope_tf()

    sur.v_to_rill = h_rill * GridGlobals.get_pixel_area()

    h, sur.rillWidth = rill.update_hb(sur.v_to_rill, RILL_RATIO, mat_efect_cont,
                                  sur.rillWidth)

    r_rill = (h * sur.rillWidth) / (sur.rillWidth + 2 * h)

    v_rill = tf.math.pow(r_rill, (2.0 / 3.0)) * 1. / n * \
             tf.math.pow(slope / 100, 0.5)

    q_rill = v_rill * h * sur.rillWidth

    v = q_rill * dt

    # original based on speed
    courant_comp = (v_rill * dt) / mat_efect_cont

    out_cond = courant_comp <= courantMax
    in_cond = v > sur.v_to_rill

    in_where = tf.where(in_cond, zeros, sur.v_to_rill - v)
    sur.v_rill_rest = tf.where(out_cond, in_where, sur.v_rill_rest)  # SUR18

    in_where = tf.where(in_cond, sur.v_to_rill, v)
    sur.vol_runoff_rill = tf.where(out_cond, in_where, sur.vol_runoff_rill)  # SUR17

    # q_rill = tf.where(sur.arr[:, :, 0] > 0, q_rill, zeros)
    v_rill = tf.where(sur.state > 0, v_rill, zeros)
    courant = tf.where(sur.state > 0, courant_comp, zeros)

    return v_rill, courant, sur.v_rill_rest, sur.vol_runoff_rill, sur.rillWidth, sur.v_to_rill


def surface_retention(bil, sur):
    """TODO.

    :param bil: TODO
    param sur: TODO
    """
    reten = sur.sur_ret
    pre_reten = reten * 1
    zeros = tf.Variable([[0] * GridGlobals.c] * GridGlobals.r,
                        dtype=tf.float64)

    cond = reten < 0
    tempBIL = tf.where(cond,
                       bil + reten, zeros)

    cond_in = tempBIL > 0
    bil_in = tf.where(cond_in, tempBIL, zeros)
    reten_in = tf.where(cond_in, zeros, tempBIL)
    bil = tf.where(cond, bil_in, bil)
    reten = tf.where(cond, reten_in, reten)

    return bil, reten, reten - pre_reten

if Globals.isRill:
    runoff = __runoff
else:
    runoff = __runoff_zero_comp_type
