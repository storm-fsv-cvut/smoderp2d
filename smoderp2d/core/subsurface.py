import numpy as np
import math


from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.core.kinematic_diffuse import Kinematic
from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger

import smoderp2d.processes.subsurface as darcy


class SubArrs:
    def __init__(self, L_sub, Ks, vg_n, vg_l, z, ele, poro):
        """Subsurface attributes.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        :param z: TODO
        :param ele: TODO
        """
        self.L_sub = L_sub
        self.h = 0.
        self.H = ele
        self.z = z
        self.slope = 0.
        self.exfiltration = 0.
        self.vol_runoff = 0.
        self.vol_runoff_pre = 0.
        self.vol_rest = 0.
        self.Ks = Ks
        self.cum_percolation = 0.
        self.percolation = 0.
        self.vg_n = vg_n
        self.vg_m = 1.0 - 1.0 / vg_n
        self.vg_l = vg_l
        self.poro = poro



# class SubsurfaceC(GridGlobals, Diffuse if Globals.diffuse else Kinematic):
class SubsurfaceC(GridGlobals, Kinematic):
    def __init__(self, L_sub, Ks, vg_n, vg_l, poro):
        """TODO.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
        GridGlobals.__init__(self)
        Kinematic.__init__(self)
        #super(SubsurfaceC, self).__init__()

        for i in range(self.r):
            for j in range(self.c):
                self.arr[i, j] = SubArrs(
                    L_sub,
                    Ks,
                    vg_n,
                    vg_l,
                    Globals.get_mat_dem(i, j) - L_sub,
                    Globals.get_mat_dem(i, j), poro)

        for i in self.rr:
            for j in self.rc[i]:
                self.arr.get_item([i, j]).slope = \
                    Globals.get_mat_dem(i, j)

        self.Kr = darcy.relative_unsat_conductivity
        self.darcy = darcy.darcy

    def slope_(self, i, j):
        a = self.arr.get_item([i - 1, j - 1]).H
        b = self.arr.get_item([i - 1, j]).H
        c = self.arr.get_item([i - 1, j + 1]).H
        d = self.arr.get_item([i, j - 1]).H
        f = self.arr.get_item([i, j + 1]).H
        g = self.arr.get_item([i + 1, j - 1]).H
        h = self.arr.get_item([i + 1, j]).H
        k = self.arr.get_item([i + 1, j + 1]).H
        dzdx = ((c + 2.0 * f + k) - (a + 2.0 * d + g)) / \
            (8.0 * self.pixel_area)
        dzdy = ((g + 2.0 * h + k) - (a + 2.0 * b + c)) / \
            (8.0 * self.pixel_area)
        nasobek = math.sqrt(pow(dzdx, 2) + pow(dzdy, 2))
        diffslope = math.atan(nasobek) * math.pi / 180

        return diffslope

    def fill_slope(self):
        self.update_H()

    def get_exfiltration(self, i, j):

        return self.arr.get_item([i, j]).exfiltration

    def bilance(self, i, j, infilt, inflow, dt):

        arr = self.arr.get_item([i, j])
        pixel_area = GridGlobals.get_pixel_area()

        # flow in and out
        bil = infilt/arr.poro + arr.vol_rest / self.pixel_area + inflow - \
            arr.vol_runoff/pixel_area

        # balance minus percolation
        percolation = self.calc_percolation(i, j, bil, dt)
        arr.cum_percolation += percolation
        arr.percolation = percolation
        bil -= percolation

        # new h after exfiltration
        arr.h, arr.exfiltration = self.calc_exfiltration(i, j, bil)

    def calc_percolation(self, i, j, bil, dt):

        arr = self.arr.get_item([i, j])

        if (bil > arr.L_sub):
            S = 1.0
        else:
            S = bil / arr.L_sub

        perc = arr.Ks * self.Kr(S, arr.vg_l, arr.vg_m) * dt
        # jj bacha
        # perc = 0
        if (perc > bil):
            perc = bil
        return perc

    def calc_exfiltration(self, i, j, bil):

        arr = self.arr.get_item([i, j])
        if (bil > arr.L_sub):
            exfilt = bil - arr.L_sub
            bil = arr.L_sub
            # print exfilt
        else:
            exfilt = 0

        return bil, exfilt

    def runoff(self, i, j, delta_t, efect_vrst):

        arr = self.arr.get_item([i, j])
        self.q_subsurface = self.darcy(arr, efect_vrst)
        arr.vol_runoff = delta_t * self.q_subsurface
        arr.vol_rest = arr.h * self.pixel_area - delta_t * self.q_subsurface

    def runoff_stream_cell(self, i, j):
        self.arr.get_item([i, j]).vol_runoff = 0.0
        self.arr.get_item([i, j]).vol_rest = 0.0
        return self.arr.get_item([i, j]).h

    def curr_to_pre(self):
        for i in self.rr:
            for j in self.rc[i]:
                self.arr.get_item([i, j]).vol_runoff_pre = self.arr.get_item(
                    [i, j]).vol_runoff

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

        if not extra_out:
            line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}'.format(
                arr.h,
                arr.vol_runoff / dt * sw,
                999,
                sep=sep
            )
        else:
            line = '{0:.4e}{sep}{1:.4e}{sep}{2:.4e}{sep}{3:.4e}{sep}{4:.4e}{sep}{5:.4e}'.format(
                arr.h,
                arr.vol_runoff / dt * sw,
                arr.vol_runoff,
                arr.vol_rest,
                arr.percolation,
                arr.exfiltration,
                sep=sep
            )
        return line


# Class
#  empty class if no subsurface flow is considered
class SubsurfacePass(GridGlobals):

    def __init__(self, L_sub, Ks, vg_n, vg_l):
        super(SubsurfacePass, self).__init__()
        # jj
        self.n = 0

        self.q_subsurface = None
        # self.arr = np.zeros([0],float)
        Logger.info("Subsurface: OFF")

    def new_inflows(self):
        pass

    def cell_runoff(self, i, j, sur):
        return 0

    def fill_slope(self):
        pass

    def get_exfiltration(self, i, j):
        return 0.0

    def bilance(self, i, j, infilt, inflow, dt):
        pass

    def runoff(self, i, j, delta_t, efect_vrst):
        pass

    def runoff_stream_cell(self, i, j):
        return 0.0

    def return_str_vals(self, i, j, sep, dt):
        return ''

    def curr_to_pre(self):
        pass


class Subsurface(SubsurfaceC if Globals.subflow else SubsurfacePass):

    def __init__(self, L_sub=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5, poro=0.5):
        Logger.info("Subsurface:")
        super(Subsurface, self).__init__(
            L_sub=L_sub,
            Ks=Ks,
            vg_n=vg_n,
            vg_l=vg_l,
            poro=poro
        )
