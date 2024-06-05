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
        :param z: elevation of the subsoil layers
        :param ele: elevation of the soil surface
        """
        # depth of the subsoil layer in meters
        self.subsoil_depth = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * subsoil_depth,
            mask=GridGlobals.masks
        )
        # water level on the subsoil layer
        self.h = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )
        # total potential of the water on the subsoil layer
        self.H = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * ele,
            mask=GridGlobals.masks
        )
        # elevation of the subsurface: DEM - subsoil_depth
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
        # has to be here in order to cell_runoff in smoderp2d/core/flow.py
        # works properly
        self.vol_runoff_rill = ma.masked_array(
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
        #van genuchgtens n
        self.vg_l = ma.masked_array(
            np.ones((GridGlobals.r, GridGlobals.c)) * vg_l,
            mask=GridGlobals.masks
        )
        #van genuchgtens m
        self.vg_m = 1 - (1 / self.vg_n)

        self.inflow_tm = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )


def get_subsurface():
    class Subsurface(GridGlobals,
                      get_diffuse() if Globals.wave == 'diffusion' else get_kinematic()):
        def __init__(self, subsoil_depth=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5):
            """Class that handles the subsurface flow.

            Subsurface flow occurs in shallow soil layer usually few tens of cm
            bellow the soil surface. The volume of water that flow is controlled 
            by the Darcy's law. The flow directions and slope can be driven by 
            D8 or mfd algorithm. The slope potentially follow the kinematic or
            diffusive wave approximation. Now, only D8 and kinematic wave is
            supported.
            

            :param subsoil_depth: of water in subsoil layer
            :param Ks: saturated hydraulic conductivity
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

            self.update_inflows(Globals.get_mat_fd())

        def slope_(self, i, j):
            """Slope implemented for diffusive wave approximation
            
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
            return self.arr.exfiltsubsoin
        def balance(self, infilt, dt):
            """calculate subsoi water balance.

            :param infilt: infiltration in current time step [L]
            :param inflow: inflows in current time step [L]
            :param dt: current time step length
            """
            arr = self.arr
            bil = infilt + arr.vol_rest / self.pixel_area + arr.inflow_tm

            percolation = self.calc_percolation(bil, dt)
            arr.cum_percolation += percolation
            bil -= percolation
            arr.percolation = percolation
            arr.h, arr.exfiltration = self.calc_exfiltration(bil)

        def calc_percolation(self, bil, dt):
            """calculated percolation to deeper soil layers.

            :param bil: subsoil water balance 
            :param dt: current time step length
            """
            arr = self.arr

            # S - saturation; if S == subsoil_depth: 
            #                       subsoil is full of water
            S = ma.where(
                bil > arr.subsoil_depth, 
                1.0,
                bil / arr.subsoil_depth
            )

            # free drainage BC at the bottom of subsoil
            perc = arr.Ks * self.Kr(S, arr.vg_l, arr.vg_m) * dt

            perc = ma.where(
               perc > bil,
               bil,
               perc
            )

            return perc

        def calc_exfiltration(self, bil):
            """Calculate amount of water then flows back to soil surface.

            :param bil: subsoil water balance
            :return: updated subsoil water balance  and exfiltrated water
            """

            arr = self.arr

            exfilt = ma.where(
                bil > arr.subsoil_depth,
                bil - arr.subsoil_depth,
                0
            )
        
            bil = ma.where(
                bil > arr.subsoil_depth,
                arr.subsoil_depth,
                bil
            )

            return bil, exfilt

        def runoff(self, delta_t, ef_counter_line, cond_state_flow):
            """Calculate the volume of subsoil runoff

            :param delta_t: current time step length
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
            :param dt: current time step length
            :return: lines with computed values
            """
            arr = self.arr
            line = '{0:.4e}{sep}{1:.4e}{sep}'\
                   '{2:.4e}{sep}{3:.4e}{sep}'\
                   '{4:.4e}{sep}{5:.4e}'.format(
                    arr.h[i][j], arr.vol_runoff[i][j] / dt, arr.vol_runoff[i][j],
                    arr.vol_rest[i][j], arr.percolation[i][j],
                    arr.exfiltration[i][j], sep=sep
            )

            return line

    return Subsurface 

class SubArrsPass:
    """TODO."""

    def __init__(self):
        """Subsurface attributes.

        """

        self.inflow_tm = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )

# Class
#  empty class if no subsurface flow is considered
def get_subsurface_pass():
    class SubsurfacePass(GridGlobals):
        """This is empty class with pass methods in case
        of not calculating subsurface flow."""

        def __init__(self, ubsoil_depth=0.010, Ks=0.001, vg_n=1.5, vg_l=0.5):
            """TODO.

            :param subsoil_depth: TODO
            :param Ks: TODO
            :param vg_n: TODO
            :param vg_l: TODO
            """
            super(SubsurfacePass, self).__init__()
            
            self.n = 0

            self.q_subsurface = None
            Logger.info("Subsurface: OFF")
            # create empty array
            self.arr = SubArrsPass()


        def new_inflows(self):
            """TODO."""
            pass

        def cell_runoff(self, i, j):
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

        def balance(self, infilt, dt):
            """TODO.

            :param infilt: TODO
            :param inflow: TODO
            :param dt: current time step length
            """
            pass

        def runoff(self, delta_t, ef_counter_line, cond_state_flow):
            """TODO.

            :param delta_t: current time step length
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
            :param dt: current time step length
            :return: TODO
            """
            return ''

        def curr_to_pre(self):
            """TODO."""
            pass


    return SubsurfacePass
