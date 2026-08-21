# @package smoderp2d.core.flow
#
#  Contains Classes and methods resolve
#  the flow type according the D8 or Mfda algorithm.
#
#  Flow algorithms itself  are stores in the package
#  smoderp2d.flow_algorithm.
#
#  Classes defined here assemble the algorithms and defines methods to
#  make D8 or mfda compatible within the SMODERP
#  framework.
#
#  Both classes can be inherited by
#  classes Kinematic or Diffuse in the
#  package smoderp2d.core.kinematic_diffuse
#
import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals

import smoderp2d.flow_algorithm.mfd as mfd
import smoderp2d.flow_algorithm.D8 as D8_
from smoderp2d.providers import Logger


class D8(object):
    """Define methods for executing the one direction flow algorithm D8.

    Can be inherited by the Classes:

     - smoderp2d.core.kinematic_diffuse.Kinematic
     - smoderp2d.core.kinematic_diffuse.Diffuse
    """

    # Poradi MUSI odpovidat seznamu inflow_directions ve
    # smoderp2d.flow_algorithm.D8.__directionsInflow(). Na nem zavisi poradi
    # scitani v inflow_all(), a tim i bitova shoda s cell_runoff().
    _INFLOW_DIRS = ((-1, 1), (-1, 0), (-1, -1), (0, -1),
                    (1, -1), (1, 0), (1, 1), (0, 1))

    def __init__(self):
        """Constructor.

        Defines inflows list which defines the flow direction for each
        cell of the DEM. The kinematic approach is used the inflows are defines
        only once in this constructor.
        """
        Logger.info("D8 flow algorithm")
        self.inflows = D8_.new_inflows(Globals.get_mat_fd())
        self._inflow_w = None

    def update_inflows(self, fd):
        """Update inflows list if the diffuse approach is used.

        In the diffusive approach the flow direction may change due to changes
        of the water level.

        :param fd: TODO
        """
        self.inflows = D8_.new_inflows(fd)
        self._inflow_w = None

    def _build_inflow_weights(self):
        """Prevede seznam inflows na vahove pole (r, c, 8) a slice pary.

        Stavi se jednou (lene, pri prvnim volani inflow_all()) a znovu po
        update_inflows() v difuznim pristupu.
        """
        r, c = GridGlobals.r, GridGlobals.c
        idx = {d: k for k, d in enumerate(self._INFLOW_DIRS)}
        w = np.zeros((r, c, len(self._INFLOW_DIRS)))
        for i in range(r):
            row = self.inflows[i]
            for j in range(c):
                for ax, bx in row[j]:
                    if i + ax < 0 or j + bx < 0:
                        # stejny guard jako v cell_runoff()
                        continue
                    w[i, j, idx[(ax, bx)]] = 1.0
        self._inflow_w = w
        self._inflow_slices = tuple(
            (slice(max(0, -ax), r - max(0, ax)),
             slice(max(0, -bx), c - max(0, bx)),
             slice(max(0, ax), r - max(0, -ax)),
             slice(max(0, bx), c - max(0, -bx)))
            for ax, bx in self._INFLOW_DIRS
        )

    def inflow_all(self):
        """Return inflow volume for the whole domain at once.

        Vektorizovana obdoba cell_runoff() volaneho pro kazdou bunku. Vysledek
        je bitove identicky - poradi scitani (pro kazdy smer nejdriv sheet,
        pak rill) odpovida puvodni smycce, neaktivni smery pricitaji presnou
        nulu.

        :returns: inflow volume from the adjacent cells for all cells
        """
        if self._inflow_w is None:
            self._build_inflow_weights()
        # step 2c: vol_runoff/vol_runoff_rill are plain ndarray now, so
        # read them directly - .data would return a memoryview instead
        # of an ndarray for a plain array, not a masked one.
        sheet = self.arr.vol_runoff
        rill = self.arr.vol_runoff_rill
        out = np.zeros((GridGlobals.r, GridGlobals.c))
        for k, (si, sj, ti, tj) in enumerate(self._inflow_slices):
            w = self._inflow_w[si, sj, k]
            out[si, sj] += w * sheet[ti, tj]
            out[si, sj] += w * rill[ti, tj]
        # step 2c: inflow_tm is plain ndarray now, out is already a
        # plain zero-initialized ndarray - no mask wrap needed.
        return out

    def cell_runoff(self, i, j):
        """Return the water volume water flows into cell i, j

        Returns values from the previous time step based on the inflows list.

        Inflows list definition is shown in the method  new_inflows() in the
        package smoderp2d.flow_algorithm.D8.

        The total inflow is sum of sheet and rill runoff volume.

        :param i: TODO
        :param j: TODO
        :returns: inflow volume from the adjacent cells
        """
        inflow_from_cells = 0.0
        for z in range(len(self.inflows[i][j])):
            ax = self.inflows[i][j][z][0]
            bx = self.inflows[i][j][z][1]
            iax = i + ax
            jbx = j + bx
            # step 2c: vol_runoff/vol_runoff_rill are plain ndarray, read
            # directly (this method is currently unused/dead - see
            # inflow_all() - but kept consistent with the rest of the
            # file rather than left referencing a stale .data pattern)
            if iax >= 0 and jbx >= 0:
                insurfflow_from_cell = self.arr.vol_runoff[iax][jbx]
            else:
                insurfflow_from_cell = 0.0
            if iax >= 0 and jbx >= 0:
                inrillflow_from_cell = self.arr.vol_runoff_rill[iax][jbx]
            else:
                inrillflow_from_cell = 0.0
            inflow_from_cells = inflow_from_cells + \
                insurfflow_from_cell + inrillflow_from_cell

        return inflow_from_cells


class Mfda(object):
    """Define methods for executing the multiple flow direction algorithm mfda.

    Can be inherited by the Classes:

    - smoderp2d.core.kinematic_diffuse.Kinematic
    - smoderp2d.core.kinematic_diffuse.Diffuse

    note: The rill flow, if computed, is always defined in terms
    of one of the direction algorithm. In the class Mfda are therefore
    defined rules for mfda which governs the sheet flow and D8
    algorithm which defines the rill flow.
    """

    def __init__(self):
        """Constructor.

        Defines inflows list which defines the flow direction for each
        cell of the DEM. The kinematic approach is used the inflows are defines
        only once in this constructor.
        TODO.
        """
        Logger.info("Multiflow direction algorithm")
        self.inflows, fd_rill = mfd.new_mfda(
            Globals.mat_dem, Globals.mat_nan, Globals.mat_fd
        )
        self.inflowsRill = D8_.new_inflows(fd_rill)

    def update_inflows(self, fd):
        """Update inflows list if the diffuse approach is used.

        In the diffusive approach the flow direction may change due to changes
        of the water level.

        :param fd: TODO
        """
        self.inflows, fd_rill = mfd.new_mfda(self.H, Globals.mat_nan, fd)
        self.inflowsRill = D8_.new_inflows(fd_rill)

    def inflow_all(self):
        """Return inflow volume for the whole domain at once.

        Pro MFD zatim skalarni fallback - vahove pole ma jinou topologii a
        navic ceka na opravu nulovych vah. Chova se presne jako puvodni
        dvojita smycka v TimeStep.do_next_h().

        :returns: inflow volume from the adjacent cells for all cells
        """
        rr, rc = GridGlobals.get_region_dim()
        # step 2c: inflow_tm is plain ndarray now, so this fallback
        # returns plain too - no mask wrap needed.
        out = np.zeros((GridGlobals.r, GridGlobals.c))
        for i in rr:
            for j in rc[i]:
                out[i, j] = self.cell_runoff(i, j)
        return out

    def cell_runoff(self, i, j, sur=True):
        """Return the water volume water flows into cell i, j

        Returns values from the previous time step based on the inflows list.

        Inflows list definition is shown in the method  new_inflows() in the
        package smoderp2d.flow_algorithm.D8.

        The total inflow is sum of sheet and rill runoff volume.

        :param i: TODO
        :param j: TODO
        :param sur: TODO
        :returns: inflow volume from the adjacent cells
        """
        # step 2c: vol_runoff is plain ndarray, read directly (.data
        # would return a memoryview, not an ndarray, for a plain array)
        if i == 0:
            inflows_up = np.zeros((GridGlobals.c, 8))
            inflows_down = self.inflows[i + 1]
            vol_runoff_up = np.zeros(GridGlobals.c)
            vol_runoff_down = self.arr.vol_runoff[i + 1]
        elif i == GridGlobals.r - 1:
            inflows_up = self.inflows[i - 1]
            inflows_down = np.zeros((GridGlobals.c, 8))
            vol_runoff_up = self.arr.vol_runoff[i - 1]
            vol_runoff_down = np.zeros(GridGlobals.c)
        else:
            inflows_up = self.inflows[i - 1]
            inflows_down = self.inflows[i + 1]
            vol_runoff_up = self.arr.vol_runoff[i - 1]
            vol_runoff_down = self.arr.vol_runoff[i + 1]

        if j == 0:
            inflows_leftup = 0
            inflows_left = 0
            inflows_leftdown = 0
            inflows_rightup = inflows_up[j + 1][3]
            inflows_right = self.inflows[i][j + 1][4]
            inflows_rightdown = inflows_down[j + 1][5]
            vol_runoff_leftup = 0
            vol_runoff_left = 0
            vol_runoff_leftdown = 0
            vol_runoff_rightup = vol_runoff_up[j + 1]
            vol_runoff_right = self.arr.vol_runoff[i][j + 1]
            vol_runoff_rightdown = vol_runoff_down[j + 1]
        elif j == GridGlobals.c - 1:
            inflows_leftup = inflows_up[j - 1][1]
            inflows_left = self.inflows[i][j - 1][0]
            inflows_leftdown = inflows_down[j - 1][7]
            inflows_rightup = 0
            inflows_right = 0
            inflows_rightdown = 0
            vol_runoff_leftup = vol_runoff_up[j - 1]
            vol_runoff_left = self.arr.vol_runoff[i][j - 1]
            vol_runoff_leftdown = vol_runoff_down[j - 1]
            vol_runoff_rightup = 0
            vol_runoff_right = 0
            vol_runoff_rightdown = 0
        else:
            inflows_leftup = inflows_up[j - 1][1]
            inflows_left = self.inflows[i][j - 1][0]
            inflows_leftdown = inflows_down[j - 1][7]
            inflows_rightup = inflows_up[j + 1][3]
            inflows_right = self.inflows[i][j + 1][4]
            inflows_rightdown = inflows_down[j + 1][5]
            vol_runoff_leftup = vol_runoff_up[j - 1]
            vol_runoff_left = self.arr.vol_runoff[i][j - 1]
            vol_runoff_leftdown = vol_runoff_down[j - 1]
            vol_runoff_rightup = vol_runoff_up[j + 1]
            vol_runoff_right = self.arr.vol_runoff[i][j + 1]
            vol_runoff_rightdown = vol_runoff_down[j + 1]

        inflow_from_cells = \
            inflows_leftup * vol_runoff_leftup + \
            inflows_up[j][2] * vol_runoff_up[j] + \
            inflows_rightup * vol_runoff_rightup + \
            inflows_left * vol_runoff_left + \
            inflows_right * vol_runoff_right + \
            inflows_leftdown * vol_runoff_leftdown + \
            inflows_down[j][6] * vol_runoff_down[j] + \
            inflows_rightdown * vol_runoff_rightdown

        if Globals.isRill and sur:
            state_ij = self.arr.state[i, j]
            for z in range(len(self.inflowsRill[i][j])):
                ax = self.inflowsRill[i][j][z][0]
                bx = self.inflowsRill[i][j][z][1]
                iax = i + ax
                jbx = j + bx

                if ma.equal(state_ij, 1) or ma.equal(state_ij, 2):
                    inflow_from_cells += self.arr.vol_runoff_rill[iax, jbx]
                    # toto jeste predelat u ryh

        return inflow_from_cells
