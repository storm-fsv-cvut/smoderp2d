"""Package contains classes and methods to compute surface processes.
"""

import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.core.stream import Stream, StreamPass
from smoderp2d.core.kinematic_diffuse import get_kinematic, get_diffuse
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
        # step 2c (numpy.ma removal): not-yet-converted fields keep
        # ma.masked_array (state, soil_type, sur_ret, h_crit, a, b,
        # h_rillPre, rillWidth). The other 15 fields below are plain
        # ndarray - every place that writes to them elsewhere in the
        # codebase has been updated (or explicitly guarded with
        # np.asarray()) so they stay plain across the whole run.
        self.state = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.sur_ret = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), sur_ret),
            mask=GridGlobals.masks
        )
        self.cur_sur_ret = np.zeros((GridGlobals.r, GridGlobals.c))
        self.cur_rain = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_sheet = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_total_new = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_total_pre = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_runoff = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vol_rest = np.zeros((GridGlobals.r, GridGlobals.c))
        self.inflow_tm = np.zeros((GridGlobals.r, GridGlobals.c))
        self.soil_type = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), inf_index),
            mask=GridGlobals.masks
        )
        self.infiltration = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_crit = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), hcrit),
            mask=GridGlobals.masks
        )
        self.a = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), a), mask=GridGlobals.masks
        )
        self.b = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), b), mask=GridGlobals.masks
        )
        self.h_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_rillPre = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_runoff_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.vel_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.v_rill_rest = np.zeros((GridGlobals.r, GridGlobals.c))
        self.rillWidth = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_to_rill = np.zeros((GridGlobals.r, GridGlobals.c))
        self.h_last_state1 = np.zeros((GridGlobals.r, GridGlobals.c))


def get_surface():
    stream_class = Stream if Globals.isStream else StreamPass
    class Surface(GridGlobals, stream_class,
                  get_diffuse() if Globals.wave == 'diffusion' else get_kinematic()):
        """Data and methods to calculate the surface and rill runoff."""

        def __init__(self):
            """The constructor.

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
                Globals.get_mat_reten(),
                Globals.get_mat_inf_index(),
                Globals.get_mat_hcrit(),
                Globals.get_mat_aa(),
                Globals.get_mat_b()
            )

            stream_class.__init__(self)

            Logger.info(
                "\tRill flow: {}".format('ON' if Globals.isRill else 'OFF')
            )

        def return_str_vals(self, i, j, sep, dt, extra_out):
            """TODO.

            :param i: row index
            :param j: col index
            :param sep: separator
            :param dt: current time step length
            :param extra_out: append extra output

            :return: TODO
            """
            arr = self.arr
            sw = Globals.slope_width

            vol_runoff = arr.vol_runoff[i, j]
            vol_runoff_rill = arr.vol_runoff_rill[i, j]

            # Water_level_[m];Flow_[m3/s];v_runoff[m3];v_rest[m3];Infiltration[];surface_retention[l]
            if not extra_out:
                line = '{0:.4e}{sep}{1:.4e}'.format(
                    arr.h_total_new[i, j],
                    (vol_runoff / dt + vol_runoff_rill / dt) *
                    sw,
                    sep=sep
                )
                bil_ = ''
            else:
                # h_sheet and vol_runoff are plain ndarray since step 2c
                velocity = np.where(
                    arr.h_sheet == 0,
                    0,
                    arr.vol_runoff / dt / (arr.h_sheet*GridGlobals.dx)
                )
                # if profile1d provider - the data in extra output are the unit
                #                          width data
                #                     if you need runoff from non-unit slope and
                #                     with extra output calculate it yourself
                line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3:.4e}{sep}' \
                       '{4:.4e}{sep}{5:.4e}{sep}{6:.4e}{sep}{7:.4e}{sep}' \
                       '{8:.4e}{sep}{9:.4e}'.format(
                    arr.h_sheet[i, j],
                    vol_runoff / dt,
                    vol_runoff,
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
                    line += '{sep}{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3:.4e}' \
                            '{sep}{4:.4e}{sep}{5:.4e}{sep}{6:.4e}{sep}' \
                            '{7:.4e}'.format(
                        arr.h_rill[i, j],
                        arr.rillWidth[i, j],
                        vol_runoff_rill / dt,
                        vol_runoff_rill,
                        arr.vel_rill[i, j],
                        arr.v_rill_rest[i, j],
                        vol_runoff / dt + vol_runoff_rill / dt,
                        vol_runoff + vol_runoff_rill,
                        sep=sep
                    )

                bil_ = arr.h_total_pre[i, j] * self.pixel_area + \
                       arr.cur_rain[i, j] * self.pixel_area + \
                       arr.inflow_tm[i, j] - \
                       (vol_runoff + vol_runoff_rill +
                        arr.infiltration[i, j] * self.pixel_area) - \
                        (arr.cur_sur_ret[i, j] * self.pixel_area) - \
                        arr.h_total_new[i, j] * self.pixel_area
                # << + arr.vol_rest + arr.v_rill_rest) +
                # (arr.vol_rest_pre + arr.v_rill_rest_pre)

            return line, bil_

    return Surface


def __runoff(sur, dt, effect_vrst):
    """Calculate the sheet and rill flow.

    :param dt: current time step length
    :param effect_vrst: TODO

    :return: TODO
    """
    h_total_pre = sur.h_total_pre
    h_crit = sur.h_crit
    state = sur.state  # da se tady podivat v jakym jsem casovym kroku a jak
    # se a

    # sur.arr.state               = update_state1(h_total_pre,h_crit,state)
    h_sheet, h_rill, h_rillPre = compute_h_hrill(
        h_total_pre, h_crit, state, sur.h_rillPre)

    q_sheet, vol_runoff, vol_rest = sheet_runoff(dt, sur.a, sur.b, h_sheet)

    v_sheet = ma.where(h_sheet > 0, q_sheet / h_sheet, 0)

    # rill runoff
    rill_runoff_results = rill_runoff(
        dt, effect_vrst, h_rill, sur.rillWidth, sur.v_rill_rest,
        sur.vol_runoff_rill
    )
    v_rill = ma.where(sur.state > 0, rill_runoff_results[0], 0)
    v_rill_rest = ma.where(sur.state > 0, rill_runoff_results[1],
                               sur.v_rill_rest)
    vol_runoff_rill = ma.where(sur.state > 0, rill_runoff_results[2],
                                   sur.vol_runoff_rill)
    rill_courant = ma.where(sur.state > 0, rill_runoff_results[3], 0)
    # vol_to_rill is plain ndarray since step 2c; guard explicitly so the
    # mixed-type ma.where() above does not silently re-wrap it.
    sur.vol_to_rill = np.asarray(
        ma.where(sur.state > 0, rill_runoff_results[4], sur.vol_to_rill)
    )
    sur.rillWidth = ma.where(sur.state > 0, rill_runoff_results[5],
                             sur.rillWidth)

    return (v_sheet, v_rill, rill_courant, h_sheet, h_rill, h_rillPre,
            vol_runoff, vol_rest, v_rill_rest, vol_runoff_rill, v_rill)


def __runoff_zero_comp_type(sur, dt, effect_vrst):
    """TODO.

    :param sur: TOD
    :param dt: current time step length
    :param effect_vrst: TODO

    :return: TODO
    """
    # sur.arr.state               = update_state1(h_total_pre,h_crit,state)
    sur.h_sheet = sur.h_total_pre

    q_sheet, vol_runoff, vol_rest = sheet_runoff(dt, sur.a, sur.b, sur.h_sheet)

    v_sheet = ma.where(sur.h_sheet > 0, q_sheet / sur.h_sheet, 0)

    v_rill = 0

    return (
        v_sheet, v_rill, 0.0, sur.h_sheet, sur.h_rill, sur.h_rillPre,
        vol_runoff, vol_rest, sur.v_rill_rest, sur.vol_runoff_rill, v_rill
    )


def update_state1(ht_1, hcrit, state):
    """TODO.

    :param ht_1: TODO
    :param hcrit: TODO
    :param state: TODO (not used)

    :return: TODO
    """
    if ht_1 > hcrit:
        if state == 0:
            return 1
    return state


def update_state(h_total_new, h_crit, h_total_pre, state, h_last_state1):
    # step 2d: h_total_new and h_total_pre are already plain ndarray
    # (step 2c); h_crit, state and h_last_state1 are still numpy.ma
    # (unconverted). Read raw .data via np.asarray() up front so the
    # whole function body below is plain ndarray arithmetic - every
    # condition and transition stays exactly as before, only ma.* ->
    # np.*.
    h_total_new = np.asarray(h_total_new)
    h_crit = np.asarray(h_crit)
    h_total_pre = np.asarray(h_total_pre)
    state = np.asarray(state)
    h_last_state1 = np.asarray(h_last_state1)

    # update state == 0
    state = np.where(
        np.logical_and(state == 0, h_total_new > h_crit), 1, state
    )

    # update state == 1
    state_1_cond = np.logical_and(state == 1, h_total_new < h_total_pre)

    state = np.where(state_1_cond, 2, state)
    h_last_state1 = np.where(state_1_cond, h_total_pre, h_last_state1)

    # update state == 2
    state = np.where(
        np.logical_and(state == 2, h_total_new > h_last_state1), 1, state
    )

    return state, h_last_state1


def compute_h_hrill(h_total_pre, h_crit, state, h_rill_pre):
    """TODO.

    :param h_total_pre: TODO (more like h_total in the implicit solution)
    :param h_crit: TODO
    :param state: TODO (not used)
    :param h_rill_pre: TODO (not used)

    :return: TODO
    """
    # step 2d: h_total_pre is already plain ndarray (step 2c); h_crit,
    # state and h_rill_pre are still numpy.ma (unconverted). Read raw
    # .data via np.asarray() up front so the whole function body below
    # is plain ndarray arithmetic - the branching structure and every
    # comparison/operator stay exactly as before, only ma.* -> np.*.
    h_total_pre = np.asarray(h_total_pre)
    h_crit = np.asarray(h_crit)
    state = np.asarray(state)
    h_rill_pre = np.asarray(h_rill_pre)

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

    return h_sheet, h_rill, h_rill_pre


def sheet_runoff(dt, a, b, h_sheet):
    """TODO.

    :param dt: current time step length
    :param a: TODO
    :param b: TODO
    :param h_sheet: TODO

    :return: TODO
    """
    q_sheet = surfacefce.shallowSurfaceKinematic(a, b, h_sheet)

    vol_runoff = q_sheet * dt * GridGlobals.get_size()[0]
    vol_rest = h_sheet * GridGlobals.get_pixel_area() - vol_runoff

    if Globals.computationType == 'implicit':
        vol_runoff = np.nan_to_num(vol_runoff, 0.0)
    
    return q_sheet, vol_runoff, vol_rest

def rill_runoff(dt, effect_vrst, h_rill, rillWidth, v_rill_rest=None,
                vol_runoff_rill=None):
    """TODO.

    :param dt: current time step length
    :param effect_vrst: TODO
    :param h_rill: TODO
    :param rillWidth: TODO
    :param v_rill_rest: TODO (not used in the implicit solution)
    :param vol_runoff_rill: TODO (not used in the implicit solution)

    :return: TODO
    """
    # numpy.ma removal: h_rill, v_rill_rest and vol_runoff_rill are
    # already plain ndarrays, while rillWidth and Globals.mat_slope are
    # still numpy.ma. The raw .data is read once through np.asarray() so
    # that the whole function body below is plain ndarray arithmetic - the
    # operations and their order are unchanged.
    nrill = np.asarray(Globals.get_mat_nrill())
    # MIND THE DTYPE: Globals.mat_slope is float32, but ma.power()
    # converted the exponent to a 0-d float64 array (getdata(0.5)), so the
    # exponentiation ran in float64. np.power(float32, 0.5) would compute
    # in float32 and differ by ~1e-7 relative. Hence the explicit float64 -
    # the upcast is lossless, so the result is bit-identical to the old one.
    slope = np.asarray(Globals.get_mat_slope(), dtype=np.float64)
    effect_vrst = np.asarray(effect_vrst)

    vol_to_rill = h_rill * GridGlobals.get_pixel_area()
    h, b = rill.update_hb(
        vol_to_rill, RILL_RATIO, effect_vrst, rillWidth
    )

    # The set of cells where numpy.ma masked everything below: a zero
    # denominator b * l in update_hb() (the division domain of
    # ma.divide()) plus the cells outside the computation area. Exactly
    # there ma.where() below took the "else" branch, because a masked
    # condition evaluates as False inside ma.where(). The condition is
    # kept explicitly so the behaviour stays bit-identical without a mask.
    rill_on = b * effect_vrst > 0
    if GridGlobals.valid is not None:
        rill_on = np.logical_and(rill_on, GridGlobals.valid)

    r_rill_num = h * b
    with np.errstate(divide='ignore', invalid='ignore'):
        r_rill = r_rill_num / (b + 2 * h)
    # same as in update_hb(): on a zero denominator ma.divide() returned
    # the numerator and masked the cell
    r_rill = np.where(np.isfinite(r_rill), r_rill, r_rill_num)

    # ma.power() masked a negative base, np.power() would give nan plus a
    # RuntimeWarning. On valid cells both r_rill and slope are
    # non-negative, so clipping at zero changes nothing; outside the area
    # the result is discarded (see rill_on).
    v_rill = np.power(np.where(r_rill > 0, r_rill, 0), (2.0 / 3.0)) \
        * 1. / nrill * np.power(np.where(slope > 0, slope, 0), 0.5)

    q_rill = v_rill * h * b

    vol_rill = q_rill * dt

    courant = (v_rill * dt) / effect_vrst

    if Globals.computationType == 'explicit':
        # celerita
        # courant = (1 + s*b/(3*(b+2*h))) * q_rill/(b*h)
        cond = np.logical_and(rill_on, courant <= courantMax)
        v_rill_rest = np.where(
            cond,
            np.where(vol_rill > vol_to_rill, 0, vol_to_rill - vol_rill),
            v_rill_rest
        )

        vol_runoff_rill = np.where(
            cond,
            np.where(vol_rill > vol_to_rill, vol_to_rill, vol_rill),
            vol_runoff_rill
        )
    else:
        # implicit branch - not exercised in the test environment (scipy
        # missing), so this rewrite was never actually run.
        # ma.filled(vol_rill, 0) zeroed exactly the masked cells, i.e. the
        # complement of rill_on.
        v_rill_rest = vol_to_rill - vol_rill

        vol_runoff_rill = np.where(rill_on, vol_rill, 0)

    return v_rill, v_rill_rest, vol_runoff_rill, courant, vol_to_rill, b

def surface_retention(bil, sur):
    """TODO.

    :param bil: TODO
    :param sur: TODO
    """
    reten = sur.sur_ret
    # step 2d: read plain-ndarray views for this function's own
    # arithmetic below. The original bil/reten objects are passed to
    # surface_retention_update() unchanged (that function is step
    # 2d-4, not yet converted), so this guard only affects the
    # bil_new computation in this function.
    reten_plain = np.asarray(reten)
    bil_plain = np.asarray(bil)
    if Globals.computationType == 'explicit':
        bil_new = np.where(
            reten_plain < 0,
            np.where(bil_plain + reten_plain > 0, bil_plain + reten_plain, 0),
            bil_plain
        )
        surface_retention_update(bil, sur)
    else:
        # For implict version bil_new is surface retention contriubution
        # to the bilance
        bil_new = np.where(
            reten_plain < 0,
            np.where(bil_plain + reten_plain > 0, reten_plain, -bil_plain),
            0
        )
    return bil_new

def surface_retention_update(h_sur, sur):
    reten = sur.sur_ret
    # step 2d: h_sur and reten (sur.sur_ret) may still be numpy.ma at
    # the call boundary - read raw .data via np.asarray() up front so
    # the whole function body below is plain ndarray arithmetic, same
    # branching as before, only ma.* -> np.*.
    reten_plain = np.asarray(reten)
    h_sur_plain = np.asarray(h_sur)
    reten_new = np.where(
        reten_plain < 0,
        np.where(h_sur_plain + reten_plain > 0, 0, h_sur_plain + reten_plain),
        reten_plain
    )

    sur.sur_ret = reten_new
    sur.cur_sur_ret = reten_new - reten_plain
    
def inflows_comp(tot_flow, list_fd):
    inflow = ma.array(
        ma.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
    )
    r = GridGlobals.r
    c = GridGlobals.c
   
    inflow[1:r, 0:c-1] += list_fd[1:r, 0:c-1, 0]*tot_flow[0:r-1, 1:c] #NE
    inflow[1:r, 0:c] += list_fd[1:r, 0:c, 1]*tot_flow[0:r-1, 0:c] #N
    inflow[1:r, 1:c] += list_fd[1:r, 1:c, 2]*tot_flow[0:r-1, 0:c-1] #NW
    inflow[0:r, 1:c] += list_fd[0:r, 1:c, 3]*tot_flow[0:r, 0:c-1] #W
    inflow[0:r-1, 1:c] += list_fd[0:r-1, 1:c, 4]*tot_flow[1:r, 0:c-1] #SW
    inflow[0:r-1, 0:c] += list_fd[0:r-1, 0:c, 5]*tot_flow[1:r, 0:c] #S
    inflow[0:r-1, 0:c-1] += list_fd[0:r-1, 0:c-1, 6]*tot_flow[1:r, 1:c] #SE
    inflow[0:r, 0:c-1] += list_fd[0:r, 0:c-1, 7]*tot_flow[0:r, 1:c] #E
    
    return inflow


if Globals.isRill:
    runoff = __runoff
else:
    runoff = __runoff_zero_comp_type
