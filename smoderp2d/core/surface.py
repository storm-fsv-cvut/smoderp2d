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
        self.h_total_new = 0.               # #5
        self.h_total_pre = 0.
        self.vol_runoff = 0.
        # self.vol_runoff_pre = float(0)
        self.vol_rest = 0.
        # self.vol_rest_pre =   float(0)
        self.inflow_tm = 0.                 # #9
        self.soil_type = inf_index
        self.infiltration = 0.
        self.h_crit = hcrit                 # #12
        self.a = a
        self.b = b
        self.h_rill = 0.
        self.h_rillPre = 0.
        self.vol_runoff_rill = 0.           # #17
        # self.vol_runoff_rill_pre= float(0)
        self.v_rill_rest = 0.
        # self.v_rill_rest_pre =  float(0)
        self.rillWidth = 0.
        self.v_to_rill = 0.                 # #20
        self.h_last_state1 = 0.
        # vol_runoff_pre #22
        # veg_true                          # #23
        # veg
        # ppl
        # pi #26


class Surface(GridGlobals, Size, Stream, Kinematic):
    """Contains data and methods to calculate the surface and rill runoff.
    """
    def __init__(self):
        """The constructor

        Make all numpy arrays and establish the inflow procedure based
        on D8 or Multi Flow Direction Algorithm method.
        """
        self.dims = 22
        GridGlobals.__init__(self)
        
        Logger.info("Surface: ON")

        self.n = 15

        arr_np = np.array(self.arr.numpy(), dtype=np.float64)

        # assign array objects
        for i in range(self.r):
            for j in range(self.c):
                arr_np[i][j][1] = Globals.get_mat_reten(i, j)
                arr_np[i][j][10] = Globals.get_mat_inf_index(i, j)
                arr_np[i][j][12] = Globals.get_mat_hcrit(i, j)
                arr_np[i][j][13] = Globals.get_mat_aa(i, j)
                arr_np[i][j][14] = Globals.get_mat_b(i, j)

        self.arr.assign(arr_np)

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
                arr[5],
                arr[7] / dt + arr[17] / dt,
                arr[7] + arr[17],
                sep=sep
            )
            bil_ = ''
        else:
            line = '{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}{sep}{7}{sep}{8}'.format(
                arr[4],
                arr[7] / dt,
                arr[7],
                arr[8],
                arr[11],
                arr[2],
                arr[0],
                arr[9],
                arr[5],
                sep=sep
            )

            if Globals.isRill:
                line += '{sep}{0}{sep}{1}{sep}{2}{sep}{3}{sep}{4}{sep}{5}{sep}{6}'.format(
                    arr[15],
                    arr[19],
                    arr[17] / dt,
                    arr[17],
                    arr[18],
                    arr[7] / dt + arr[17] / dt,
                    arr[7] + arr[17],
                    sep=sep
                )

            bil_ = arr[6] * self.pixel_area + \
                   arr[3] * self.pixel_area + \
                   arr[9] - \
                   (arr[7] + arr[17] + \
                    arr[11] * self.pixel_area) - \
                    (arr[2] * self.pixel_area) - \
                    arr[5] * self.pixel_area
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

    h_sheet, h_rill, h_rillPre = compute_h_hrill(
        sur.arr[:, :, 6], sur.arr[:, :, 12], sur.arr[:, :, 0],
        sur.arr[:, :, 16], zeros)

    q_sheet, vol_runoff, vol_rest = sheet_runoff(sur, dt, h_sheet)

    v_sheet = tf.where(h_sheet > 0.0, q_sheet / h_sheet, zeros)

    v_rill, rill_courant, v_rill_rest, vol_runoff_rill, rillWidth, v_to_rill \
        = rill_runoff(sur, dt, mat_efect_cont, h_rill, zeros)
    
    return h_sheet, h_rill, h_rillPre, v_sheet, v_rill, rill_courant, \
           v_rill_rest, vol_runoff_rill, vol_runoff, vol_rest, rillWidth, \
           v_to_rill


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
    h_rill_pre = tf.where(cond3, zeros, cond_in_compute_h_hrill)  # SUR16

    return h_sheet, h_rill, h_rill_pre
    
def sheet_runoff(sur, dt, h_sheet):
    """TODO.

    :param sur: TODO
    :param dt: TODO
    
    :return: TODO
    """
    q_sheet = surfacefce.shallowSurfaceKinematic(
        sur.arr[:, :, 13], sur.arr[:, :, 14], h_sheet)
    # TODO: Do I really need to recast?
    q_sheet = tf.dtypes.cast(q_sheet, tf.float32)
    vol_runoff = dt * q_sheet * GridGlobals.get_size()[0]
    vol_rest = h_sheet * GridGlobals.get_pixel_area() - vol_runoff  # SUR7

    return q_sheet, vol_runoff, vol_rest

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

    v_to_rill = h_rill * GridGlobals.get_pixel_area()

    h, rillWidth = rill.update_hb(v_to_rill, RILL_RATIO, mat_efect_cont,
                                  sur.arr[:, :, 19])

    r_rill = (h * rillWidth) / (rillWidth + 2 * h)

    v_rill = tf.math.pow(r_rill, (2.0 / 3.0)) * 1. / n * \
             tf.math.pow(slope / 100, 0.5)

    q_rill = v_rill * h * rillWidth

    v = q_rill * dt

    # original based on speed
    courant_comp = (v_rill * dt) / mat_efect_cont

    out_cond = courant_comp <= courantMax
    in_cond = v > v_to_rill

    in_where = tf.where(in_cond, zeros, v_to_rill - v)
    v_rill_rest = tf.where(out_cond, in_where, sur.arr[:, :, 18])  # SUR18

    in_where = tf.where(in_cond, v_to_rill, v)
    vol_runoff_rill = tf.where(out_cond, in_where, sur.arr[:, :, 17])  # SUR17

    # q_rill = tf.where(sur.arr[:, :, 0] > 0, q_rill, zeros)
    v_rill = tf.where(sur.arr[:, :, 0] > 0, v_rill, zeros)
    courant = tf.where(sur.arr[:, :, 0] > 0, courant_comp, zeros)

    return v_rill, courant, v_rill_rest, vol_runoff_rill, rillWidth, v_to_rill


def surface_retention(bil, sur):
    """TODO.
    
    :param bil: TODO
    param sur: TODO
    """
    reten = sur[:, :, 1]
    pre_reten = reten
    zeros = tf.Variable([[0] * GridGlobals.c] * GridGlobals.r,
                        dtype=tf.float32)

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
