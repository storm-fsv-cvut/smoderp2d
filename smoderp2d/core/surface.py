"""Package contains classes and methods to compute surface processes.
"""

import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
if Globals.isStream:
    from smoderp2d.core.stream import Stream
else:
    from smoderp2d.core.stream import StreamPass as Stream
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
        self.state = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.sur_ret = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), sur_ret),
            mask=GridGlobals.masks
        )
        self.cur_sur_ret = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.cur_rain = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h_sheet = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h_total_new = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h_total_pre = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_runoff = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_rest = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.inflow_tm = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.soil_type = ma.masked_array(
            np.full((GridGlobals.r, GridGlobals.c), inf_index),
            mask=GridGlobals.masks
        )
        self.infiltration = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
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
        self.h_rill = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h_rillPre = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_runoff_rill = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vel_rill = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.v_rill_rest = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.rillWidth = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_to_rill = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.h_last_state1 = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )


def get_surface():
    class Surface(GridGlobals, Stream,
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

            Stream.__init__(self)

            Logger.info(
                "\tRill flow: {}".format('ON' if Globals.isRill else 'OFF')
            )

        def return_str_vals(self, i, j, sep, dt, extra_out):
            """TODO.

            :param i: row index
            :param j: col index
            :param sep: separator
            :param dt: TODO
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
                velocity = ma.where(
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


def update_state1(ht_1, hcrit, state):
    """TODO.

    :param ht_1: TODO
    :param hcrit: TODO
    :param state: TODO (not used)

    :return: TODO
    """
    state = ma.where(ht_1 > hcrit,ma.where(state == 0, 1, state), state)
    # if ht_1 > hcrit:
    #     if state == 0:
    #         return 1
    return state


def update_state(h_total_new, h_crit, h_total_pre, state, h_last_state1):
    # update state == 0
    state = ma.where(
        ma.logical_and(
            state == 0, h_total_new > h_crit
        ),
        1,
        state
    )

    # update state == 1
    state_1_cond = ma.logical_and(state == 1, h_total_new < h_total_pre)

    state = ma.where(state_1_cond, 2, state)
    h_last_state1 = ma.where(state_1_cond, h_total_pre, h_last_state1)

    # update state == 2
    state = ma.where(
        ma.logical_and(state == 2, h_total_new > h_last_state1), 1, state
    )

    return state             



# New version for implicit scheme
def compute_h_hrill(h_total, h_crit, state,h_rill_pre):
    
    h_rill = ma.where(
        state == 0,
        0,
        ma.where(
            state == 1,
            ma.maximum(h_total - h_crit, 0),
            ma.where(h_total > h_rill_pre, h_rill_pre, h_total)
        )
    )
    
    h_sheet = ma.where(
        state == 0,
        h_total,
        ma.where(
            state == 1,
            ma.minimum(h_crit, h_total),
            ma.where(h_total > h_rill_pre, h_total - h_rill_pre, 0)
        )
    )
    
    return h_sheet, h_rill


def compute_h_rill_pre( h_rill_pre,h_rill,state): #h_rill_pre is depth of rill
    h_rill_pre = ma.where(
        state == 0,
        0,
        ma.where(
            state == 1,
            h_rill,
            h_rill_pre
        )
            )
    return h_rill_pre


def sheet_runoff(a, b, h_sheet):
    
    q_sheet = surfacefce.shallowSurfaceKinematic(a, b, h_sheet)

    vol_runoff = q_sheet * GridGlobals.get_size()[0]
    
    vol_runoff = np.nan_to_num(vol_runoff, 0.0)
    
    return vol_runoff

def rill_runoff(dt,   h_rill, effect_vrst, rillWidth ):
    """TODO.

    :param dt: TODO
    :param effect_vrst: TODO
    :param h_rill: TODO
    :param rillWidth: TODO
    :param v_rill_rest: TODO
    :param vol_runoff_rill: TODO
    """

    nrill = Globals.get_mat_nrill()
    slope = Globals.get_mat_slope()

    vol_to_rill = h_rill * GridGlobals.get_pixel_area()
    h, b = rill.update_hb(
        vol_to_rill, RILL_RATIO, effect_vrst, rillWidth
    )
    r_rill = (h * b) / (b + 2 * h)

    v_rill = ma.power(r_rill, (2.0 / 3.0)) * 1. / nrill * ma.power(slope, 0.5)

    q_rill = v_rill * h * b

    vol_runoff_rill = ma.filled(q_rill,0)
        
    return vol_runoff_rill


def surface_retention_impl(h_sur, reten_old):
    reten = reten_old
    # print(reten.max(), reten.min())
    
    h_ret = ma.where(reten<0, 
                     ma.where(h_sur+reten > 0, reten, 
                     -h_sur),
                     0
                     )
    
    return h_ret

def surface_retention_update(h_sur, sur):
    reten = sur.sur_ret
    reten_new = ma.where(
        reten < 0,
        ma.where(h_sur + reten > 0, 0, h_sur + reten),
        reten
    )

    sur.sur_ret = reten_new
    sur.cur_sur_ret = reten_new - reten
    
def inflows_comp(tot_flow, list_fd):
    inflow = ma.array(ma.zeros((GridGlobals.r, GridGlobals.c)),mask=GridGlobals.masks)
    r = GridGlobals.r
    c = GridGlobals.c
   
    inflow[1:r,0:c-1] += list_fd[1:r,0:c-1,0]*tot_flow[0:r-1,1:c] #NE
    inflow[1:r,0:c] += list_fd[1:r,0:c,1]*tot_flow[0:r-1,0:c] #N
    inflow[1:r,1:c] += list_fd[1:r,1:c,2]*tot_flow[0:r-1,0:c-1] #NW
    inflow[0:r,1:c] += list_fd[0:r,1:c,3]*tot_flow[0:r,0:c-1] #W
    inflow[0:r-1,1:c] += list_fd[0:r-1,1:c,4]*tot_flow[1:r,0:c-1] #SW
    inflow[0:r-1,0:c] += list_fd[0:r-1,0:c,5]*tot_flow[1:r,0:c] #S
    inflow[0:r-1,0:c-1] += list_fd[0:r-1,0:c-1,6]*tot_flow[1:r,1:c] #SE
    inflow[0:r,0:c-1] += list_fd[0:r,0:c-1,7]*tot_flow[0:r,1:c] #E
    
    return inflow

