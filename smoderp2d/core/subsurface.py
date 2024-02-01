import numpy as np
import numpy.ma as ma
import math


from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.core.kinematic_diffuse import get_diffuse, get_kinematic
from smoderp2d.providers import Logger

import smoderp2d.processes.subsurface as darcy


class SubArrs:
<<<<<<< HEAD
    def __init__(self, L_sub, Ks, vg_n, vg_l, z, ele, poro):
=======
    """TODO."""

    def __init__(self, L_sub, Ks, vg_n, vg_l, z, ele):
>>>>>>> master
        """Subsurface attributes.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        :param z: TODO
        :param ele: TODO
        """
<<<<<<< HEAD
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
=======
        self.L_sub = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * L_sub,
            mask=GridGlobals.masks
        )
        self.h = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.H = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * ele,
            mask=GridGlobals.masks
        )
        self.z = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * z, mask=GridGlobals.masks
        )
        self.slope = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.exfiltration = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_runoff = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_runoff_pre = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vol_rest = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.Ks = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * Ks, mask=GridGlobals.masks
        )
        self.cum_percolation = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.percolation = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        self.vg_n = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * vg_n,
            mask=GridGlobals.masks
        )
        self.vg_m = 1 - (1 / self.vg_n)
        self.vg_l = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * vg_l,
            mask=GridGlobals.masks
        )


class SubsurfaceC(GridGlobals, get_diffuse() if Globals.diffuse else get_kinematic()):
    def __init__(self, L_sub, Ks, vg_n, vg_l):
>>>>>>> master
        """TODO.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
        GridGlobals.__init__(self)
<<<<<<< HEAD
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
=======

        self.arr = SubArrs(
            L_sub,
            Ks,
            vg_n,
            vg_l,
            Globals.mat_dem - L_sub,
            Globals.mat_dem)

        self.arr.slope = Globals.mat_slope
>>>>>>> master

        self.Kr = darcy.relative_unsat_conductivity
        self.darcy = darcy.darcy

    def slope_(self, i, j):
        """TODO.

        :param i: TODO
        :param j: TODO
        :return: TODO
        """
        a = self.arr.H[i - 1, j - 1]
        b = self.arr.H[i - 1, j]
        c = self.arr.H[i - 1, j + 1]
        d = self.arr.H[i, j - 1]
        f = self.arr.H[i, j + 1]
        g = self.arr.H[i + 1, j - 1]
        h = self.arr.H[i + 1, j]
        k = self.arr.H[i + 1, j + 1]
        dzdx = ((c + 2.0 * f + k) - (a + 2.0 * d + g)) / \
            (8.0 * self.pixel_area)
        dzdy = ((g + 2.0 * h + k) - (a + 2.0 * b + c)) / \
            (8.0 * self.pixel_area)
        nasobek = math.sqrt(pow(dzdx, 2) + pow(dzdy, 2))
        diffslope = math.atan(nasobek) * math.pi / 180

        return diffslope

    def fill_slope(self):
        """TODO."""
        self.update_H()

    def get_exfiltration(self):
        """TODO."""
        return self.arr.exfiltration

    def bilance(self, infilt, inflow, dt):
        """TODO.

<<<<<<< HEAD
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
=======
        :param infilt: TODO
        :param inflow: TODO
        :param dt: TODO
        """
        arr = self.arr
        bil = infilt + arr.vol_rest / self.pixel_area + inflow

        percolation = self.calc_percolation(bil, dt)
        arr.cum_percolation += percolation
        bil -= percolation
        arr.percolation = percolation
        arr.h, arr.exfiltration = self.calc_exfiltration(bil)
>>>>>>> master

    def calc_percolation(self, bil, dt):
        """TODO.

        :param bil: TODO
        :param dt: TODO
        """
        arr = self.arr

        if bil > arr.L_sub:
            S = 1.0
        else:
            S = bil / arr.L_sub

        perc = arr.Ks * self.Kr(S, arr.vg_l, arr.vg_m) * dt
        # jj bacha
        # perc = 0
        if perc > bil:
            perc = bil
        return perc

    def calc_exfiltration(self, bil):
        """TODO.

<<<<<<< HEAD
        arr = self.arr.get_item([i, j])
        if (bil > arr.L_sub):
=======
        :param bil: TODO
        """
        arr = self.arr
        if bil > arr.L_sub:
>>>>>>> master
            exfilt = bil - arr.L_sub
            bil = arr.L_sub
        else:
            exfilt = 0

        return bil, exfilt

    def runoff(self, delta_t, effect_vrst):
        """TODO.

<<<<<<< HEAD
        arr = self.arr.get_item([i, j])
        self.q_subsurface = self.darcy(arr, efect_vrst)
=======
        :param delta_t: TODO
        :param effect_vrst: TODO
        """
        arr = self.arr
        self.q_subsurface = self.darcy(arr, effect_vrst)
>>>>>>> master
        arr.vol_runoff = delta_t * self.q_subsurface
        arr.vol_rest = arr.h * self.pixel_area - delta_t * self.q_subsurface

    def runoff_stream_cell(self, indices):
        """TODO.

        :param indices: TODO
        """
        self.arr.vol_runoff[indices] = 0.0
        self.arr.vol_rest[indices] = 0.0
        return ma.where(indices, self.arr.h, 0)

    def curr_to_pre(self):
<<<<<<< HEAD
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
=======
        """TODO."""
        self.arr.vol_runoff_pre = self.arr.vol_runoff

    def return_str_vals(self, i, j, sep, dt):
        """TODO.

        :param i: TODO
        :param j: TODO
        :param sep: TODO
        :param dt: TODO
        :return: TODO
        """
        arr = self.arr
        #  ';Sub_Water_level_[m];Sub_Flow_[m3/s];Sub_V_runoff[m3];Sub_V_rest[m3];Percolation[],exfiltration[];'
        line = str(
            arr.h) + sep + str(
                arr.vol_runoff / dt) + sep + str(
            arr.vol_runoff) + sep + str(
                arr.vol_rest) + sep + str(
                    arr.percolation) + sep + str(
                        arr.exfiltration)
>>>>>>> master
        return line


# Class
#  empty class if no subsurface flow is considered
class SubsurfacePass(GridGlobals):
    """TODO."""

    def __init__(self, L_sub, Ks, vg_n, vg_l):
        """TODO.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
        super(SubsurfacePass, self).__init__()
        # jj
        self.n = 0

        self.q_subsurface = None
        # self.arr = np.zeros([0],float)
        Logger.info("Subsurface: OFF")

    def new_inflows(self):
        """TODO."""
        pass

    def cell_runoff(self, i, j, sur):
        """TODO.

        :param i: TODO
        :param j: TODO
        :param sur: TODO
        """
        return 0

    def fill_slope(self):
        """TODO."""
        pass

    def get_exfiltration(self):
        """TODO."""
        return ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )

    def bilance(self, infilt, inflow, dt):
        """TODO.

        :param infilt: TODO
        :param inflow: TODO
        :param dt: TODO
        """
        pass

    def runoff(self, delta_t, effect_vrst):
        """TODO.

        :param delta_t: TODO
        :param effect_vrst: TODO
        """
        pass

    def runoff_stream_cell(self, indices):
        """TODO.

        :param indices: TODO
        """
        return 0.0

    def return_str_vals(self, i, j, sep, dt):
        """TODO.

        :param i: TODO
        :param j: TODO
        :param sep: TODO
        :param dt: TODO
        :return: TODO
        """
        return ''

    def curr_to_pre(self):
        """TODO."""
        pass


class Subsurface(SubsurfaceC if Globals.subflow else SubsurfacePass):
    """TODO."""

<<<<<<< HEAD
    def __init__(self, L_sub=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5, poro=0.5):
=======
    def __init__(self, L_sub=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5):
        """TODO.

        :param L_sub: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
>>>>>>> master
        Logger.info("Subsurface:")
        super(Subsurface, self).__init__(
            L_sub=L_sub,
            Ks=Ks,
            vg_n=vg_n,
            vg_l=vg_l,
            poro=poro
        )
