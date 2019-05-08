import numpy as np
import math
import tensorflow as tf


from smoderp2d.core.general import GridGlobals, Globals, Size
from smoderp2d.core.kinematic_diffuse import Kinematic
from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger

import smoderp2d.processes.subsurface as darcy

class SubArrs:

    L_sub = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    h = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    H = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    z = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    slope = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    exfiltration = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vol_runoff = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vol_runoff_pre = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vol_rest = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    Ks = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    cum_percolation = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    percolation = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vg_n = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vg_m = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)
    vg_l = tf.Variable(
        [[0] * GridGlobals.c] * GridGlobals.r, dtype=tf.float32)


class SubsurfaceC(GridGlobals, Diffuse if Globals.diffuse else Kinematic,
                  Size, SubArrs):
    def __init__(self, L_sub, Ks, vg_n, vg_l):
        """TODO.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
        GridGlobals.__init__()

        self.initialize_variables(L_sub, Ks, vg_n, vg_l)

        self.Kr = darcy.relative_unsat_conductivity
        self.darcy = darcy.darcy

    def initialize_variables(self, L_sub, Ks, vg_n, vg_l):
        self.L_sub = tf.Variable([[L_sub] * GridGlobals.c] * GridGlobals.r,
                                 dtype=tf.float32)
        self.H = mat_dem
        self.z = mat_dem - self.L_sub
        self.slope = mat_slope
        self.Ks = tf.Variable(
            [[Ks] * GridGlobals.c] * GridGlobals.r,
            dtype=tf.float32)
        self.vg_n = tf.Variable(
            [[vg_n] * GridGlobals.c] * GridGlobals.r,
            dtype=tf.float32)
        self.vg_m = tf.Variable(
            [[1.0 - 1.0 / vg_n] * GridGlobals.c] * GridGlobals.r,
            dtype=tf.float32)
        self.vg_l = tf.Variable(
            [[vg_l] * GridGlobals.c] * GridGlobals.r,
            dtype=tf.float32)

    def slope_(self, i, j):
        a = self.H[i - 1][j - 1]
        b = self.H[i - 1][j]
        c = self.H[i - 1][j + 1]
        d = self.H[i][j - 1]
        f = self.H[i][j + 1]
        g = self.H[i + 1][j - 1]
        h = self.H[i + 1][j]
        k = self.H[i + 1][j + 1]
        dzdx = ((c + 2.0 * f + k) - (a + 2.0 * d + g)) / \
            (8.0 * self.pixel_area)
        dzdy = ((g + 2.0 * h + k) - (a + 2.0 * b + c)) / \
            (8.0 * self.pixel_area)
        nasobek = math.sqrt(pow(dzdx, 2) + pow(dzdy, 2))
        diffslope = math.atan(nasobek) * math.pi / 180

        return diffslope

    def fill_slope(self):
        self.update_H()

    def get_exfiltration(self):

        return self.exfiltration

    def bilance(self, i, j, infilt, inflow, dt):

        arr = self.arr[i][j]
        bil = infilt + self.vol_rest[i, j] / self.pixel_area + inflow

        # print bil, infilt , arr.vol_rest/self.pixel_area , inflow
        percolation = self.calc_percolation(i, j, bil, dt)
        self.cum_percolation[i, j] += percolation
        bil -= percolation
        # print bil,
        self.percolation[i, j] = percolation
        self.h[i, j], self.exfiltration[i, j] = self.calc_exfiltration(i, j, bil)
        # print arr.h
        # print arr.h, infilt, arr.vol_rest/self.pixel_area, inflow

    def calc_percolation(self, i, j, bil, dt):

        arr = self.arr[i][j]

        if (bil > self.L_sub[i, j]):
            S = 1.0
        else:
            S = bil / self.L_sub[i, j]

        perc = self.Ks[i, j] * self.Kr(S, self.vg_l[i, j], self.vg_m[i, j]) * dt
        # jj bacha
        # perc = 0
        if (perc > bil):
            perc = bil
        return perc

    def calc_exfiltration(self, i, j, bil):

        arr = self.arr[i][j]
        if (bil > self.L_sub[i, j]):
            # print bil
            exfilt = bil - self.L_sub[i, j]
            bil = self.L_sub[i, j]
            # print exfilt
        else:
            exfilt = 0

        return bil, exfilt

    def runoff(self, subarr, delta_t, mat_efect_cont):

        self.q_subsurface = self.darcy(subarr, mat_efect_cont)
        sub_vol_runoff = delta_t * self.q_subsurface  # SUBARR6
        sub_vol_rest = self.h * self.pixel_area - \
                       delta_t * self.q_subsurface  # SUBARR8

        return sub_vol_runoff, sub_vol_rest

    def runoff_stream_cell(self, zeros):
        self.vol_runoff = zeros
        self.vol_rest = zeros
        return self.h

    def curr_to_pre(self):
        for i in self.rr:
            for j in self.rc[i]:
                self.vol_runoff_pre[i, j] = self.vol_runoff[i, j]

    def return_str_vals(self, i, j, sep, dt):
        arr = self.arr[i][j]
         #';Sub_Water_level_[m];Sub_Flow_[m3/s];Sub_V_runoff[m3];Sub_V_rest[m3];Percolation[],exfiltration[];'
        line = str(
            self.h[i, j]) + sep + str(
                self.vol_runoff[i, j] / dt) + sep + str(
            self.vol_runoff[i, j]) + sep + str(
                self.vol_rest[i, j]) + sep + str(
                    self.percolation[i, j]) + sep + str(
                        self.exfiltration[i, j])
        return line


# Class
#  empty class if no subsurface flow is considered
class SubsurfacePass(GridGlobals, Size, SubArrs):

    def __init__(self, L_sub, Ks, vg_n, vg_l):
        super(SubsurfacePass, self).__init__()
        # jj
        self.n = 0

        self.q_subsurface = None
        # self.arr = np.zeros([0],float)

        self.initialize_variables(L_sub, Ks, vg_n, vg_l)

        Logger.info("Subsurface: OFF")

    def initialize_variables(self, L_sub, Ks, vg_n, vg_l):
        pass

    def new_inflows(self):
        pass

    def cell_runoff(self, i, j, sur):
        return 0

    def fill_slope(self):
        pass

    def get_exfiltration(self):
        return tf.Variable([[0] * GridGlobals.c] * GridGlobals.r,
                           dtype=tf.float32)

    def bilance(self, i, j, infilt, inflow, dt):
        pass

    def runoff(self, subarr, delta_t, efect_vrst):
        return self.vol_runoff, self.vol_rest

    def runoff_stream_cell(self, zeros):
        return zeros

    def return_str_vals(self, i, j, sep, dt):
        return ''

    def curr_to_pre(self):
        pass


class Subsurface(SubsurfaceC if Globals.subflow else SubsurfacePass):

    def __init__(self, L_sub=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5):
        self.dims = 0
        Logger.info("Subsurface:")
        super(Subsurface, self).__init__(
            L_sub=L_sub,
            Ks=Ks,
            vg_n=vg_n,
            vg_l=vg_l
        )
