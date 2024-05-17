import numpy as np
import numpy.ma as ma
import math


from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.core.kinematic_diffuse import get_diffuse, get_kinematic
from smoderp2d.providers import Logger

import smoderp2d.processes.subsurface as darcy


class SubArrs:
    """TODO."""

    def __init__(self, subsoil_depth, Ks, vg_n, vg_l, z, ele):
        """Subsurface attributes.

        :param subsoil_depth: depth of subsoil layer
        :param Ks: saturated hydrulic conductivity
        :param vg_n: van genuchten parameter 
        :param vg_l: van genuchten parameter
        :param z: ???
        :param ele: elevatin of subsoil
        """
        # amount of water in subsoil = h / porosity
        self.subsoil_depth = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * subsoil_depth,
            mask=GridGlobals.masks
        )
        # water level on the subsoil layer
        self.h = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # total optantial of the water on the subsoil layer
        self.H = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * ele,
            mask=GridGlobals.masks
        )
        self.z = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * z, mask=GridGlobals.masks
        )
        # slope of the subsoil layer = slope of surface
        self.slope = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # if subsoil layer is full the water exfiltrates
        self.exfiltration = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # volume of subsurface runoff
        self.vol_runoff = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # volume of subsurface runoff in cell from previous time step
        self.vol_runoff_pre = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # remaining water in the subsurface
        self.vol_rest = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # saturated hydraulic conductivity 
        self.Ks = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * Ks, mask=GridGlobals.masks
        )
        # cumulative percolation (for percolation see few lines bellow)
        self.cum_percolation = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # water that infiltrates to deeper soil layers
        self.percolation = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        #van genuchgtens n
        self.vg_n = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * vg_n,
            mask=GridGlobals.masks
        )
        #van genuchgtens m
        self.vg_m = 1 - (1 / self.vg_n)


class SubsurfaceC(GridGlobals,
                  get_diffuse() if Globals.wave == 'diffusion' else get_kinematic()):
    def __init__(self, subsoil_depth, Ks, vg_n, vg_l = 0.5):
        """Class that handles the subsurface flow.

        Subsurface flow occurs in shallow soil layer usually few tens of cm
        bellow the soil surface. The volume of water that flow is controlled 
        by the Darcy's law. The flow directions and slope can be driven by 
        D8 or mfd algorithm. The slope potentially follow the kinematic or
        diffusive wave approximation. Now, only D8 and kinematic wave is
        supported.
        

        :param subsoil_depth: of water in subsoil layer
        :param Ks: saturated hydrulic conductivity
        :param vg_n: van genuchten parameter 
        :param vg_l: van genuchten parameter usually = 0.5
        """
        GridGlobals.__init__(self)

        Logger.info("Subsurface: ON")

        self.arr = SubArrs(
            subsoil_depth,
            Ks,
            vg_n,
            vg_l,
            Globals.mat_dem - subsoil_depth,
            Globals.mat_dem)

        self.arr.slope = Globals.mat_slope

        self.Kr = darcy.relative_unsat_conductivity
        self.darcy = darcy.darcy

    def slope_(self, i, j):
        """Slope implemented for diffusitve wave approximation
        
        It is not used in kinematic wave approximation.

        :param i: i th element
        :param j: j th element 
        :return: slope
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
        """Update H (=z + h) for next slope calculation."""
        self.update_H()

    def get_exfiltration(self):
        """Return the current exfiltration amount at given time step."""
        return self.arr.exfiltration

    def bilance(self, infilt, inflow, dt):
        """calculate subsoi water balance.

        :param infilt: infiltration in current time step [L]
        :param inflow: inflows in current time step [L]
        :param dt: current time step
        """
        arr = self.arr
        bil = infilt + arr.vol_rest / self.pixel_area + inflow

        percolation = self.calc_percolation(bil, dt)
        arr.cum_percolation += percolation
        bil -= percolation
        arr.percolation = percolation
        arr.h, arr.exfiltration = self.calc_exfiltration(bil)

    def calc_percolation(self, bil, dt):
        """calculated percolation to deeper soil layers.

        :param bil: subsoil water balance 
        :param dt: time step 
        """
        arr = self.arr

        if bil > arr.subsoil_depth:
            S = 1.0
        else:
            S = bil / arr.subsoil_depth

        perc = arr.Ks * self.Kr(S, arr.vg_l, arr.vg_m) * dt
        # jj bacha
        # perc = 0
        if perc > bil:
            perc = bil
        return perc

    def calc_exfiltration(self, bil):
        """Calculate amount of water then flows back to soil surface.

        :param bil: subsoil water balance
        :return: updated subsoil water balance  and exfiltrated water
        """

        arr = self.arr
        if bil > arr.subsoil_depth:
            exfilt = bil - arr.subsoil_depth
            bil = arr.subsoil_depth
        else:
            exfilt = 0

        return bil, exfilt

    def runoff(self, delta_t, ef_counter_line, cond_state_flow):
        """Calculate the volume of subsoil runoff

        :param delta_t: time step
        :param ef_counter_line: effective counter line 
        """
        arr = self.arr
        subflow = self.darcy(arr, ef_counter_line) 
        self.q_subsurface = ma.where(cond_state_flow, subflow , 0)
        arr.vol_runoff = delta_t * self.q_subsurface
        arr.vol_rest = arr.h * self.pixel_area - delta_t * self.q_subsurface

    def runoff_stream_cell(self, indices):
        """Zeros in cells that are where stream reach is.

        :param indices: what cell in arrays is where the stream is
        """
        self.arr.vol_runoff[indices] = 0.0
        self.arr.vol_rest[indices] = 0.0
        return ma.where(indices, self.arr.h, 0)

    def curr_to_pre(self):
        """At the end of time step calculation the runoff water volume is
        stored in vol_runoff_pre."""
        self.arr.vol_runoff_pre = self.arr.vol_runoff

    def return_str_vals(self, i, j, sep, dt):
        """Returns values stored in i j cell for io.

        :param i: i th cell
        :param j: j th cell
        :param sep: separator to file
        :param dt: time step
        :return: TODO
        """
        arr = self.arr
        line = str(
            arr.h) + sep + str(
                arr.vol_runoff / dt) + sep + str(
            arr.vol_runoff) + sep + str(
                arr.vol_rest) + sep + str(
                    arr.percolation) + sep + str(
                        arr.exfiltration)
        return line


# Class
#  empty class if no subsurface flow is considered
class SubsurfacePass(GridGlobals):
    """TODO."""

    def __init__(self, subsoil_depth, Ks, vg_n, vg_l):
        """TODO.

        :param subsoil_depth: TODO
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

    def runoff(self, delta_t, ef_counter_line):
        """TODO.

        :param delta_t: TODO
        :param ef_counter_line: TODO
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

    def __init__(self, subsoil_depth=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5):
        """TODO.

        :param subsoil_depth: TODO
        :param Ks: TODO
        :param vg_n: TODO
        :param vg_l: TODO
        """
        Logger.info("Subsurface:")
        super(Subsurface, self).__init__(
            subsoil_depth=subsoil_depth,
            Ks=Ks,
            vg_n=vg_n,
            vg_l=vg_l
        )
