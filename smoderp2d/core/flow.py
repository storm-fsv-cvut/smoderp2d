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

    def __init__(self):
        """Constructor.

        Defines inflows list which defines the flow direction for each
        cell of the DEM. The kinematic approach is used the inflows are defines
        only once in this constructor.
        """
        Logger.info("D8 flow algorithm")
        self.inflows = D8_.new_inflows(Globals.get_mat_fd())

    def update_inflows(self, fd):
        """Update inflows list if the diffuse approach is used.

        In the diffusive approach the flow direction may change due to changes
        of the water level.

        :param fd: TODO
        """
        self.inflows = D8_.new_inflows(fd)

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
            if iax >= 0 and jbx >= 0:
                insurfflow_from_cell = self.arr.vol_runoff.data[iax][jbx]
            else:
                insurfflow_from_cell = 0.0
            if iax >= 0 and jbx >= 0:
                inrillflow_from_cell = self.arr.vol_runoff_rill.data[iax][jbx]
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
        if i == 0:
            inflows_up = np.zeros((GridGlobals.c, 8))
            inflows_down = self.inflows[i + 1]
            vol_runoff_up = np.zeros(GridGlobals.c)
            vol_runoff_down = self.arr.vol_runoff.data[i + 1]
        elif i == GridGlobals.r - 1:
            inflows_up = self.inflows[i - 1]
            inflows_down = np.zeros((GridGlobals.c, 8))
            vol_runoff_up = self.arr.vol_runoff.data[i - 1]
            vol_runoff_down = np.zeros(GridGlobals.c)
        else:
            inflows_up = self.inflows[i - 1]
            inflows_down = self.inflows[i + 1]
            vol_runoff_up = self.arr.vol_runoff.data[i - 1]
            vol_runoff_down = self.arr.vol_runoff.data[i + 1]

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
            vol_runoff_right = self.arr.vol_runoff.data[i][j + 1]
            vol_runoff_rightdown = vol_runoff_down[j + 1]
        elif j == GridGlobals.c - 1:
            inflows_leftup = inflows_up[j - 1][1]
            inflows_left = self.inflows[i][j - 1][0]
            inflows_leftdown = inflows_down[j - 1][7]
            inflows_rightup = 0
            inflows_right = 0
            inflows_rightdown = 0
            vol_runoff_leftup = vol_runoff_up[j - 1]
            vol_runoff_left = self.arr.vol_runoff.data[i][j - 1]
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
            vol_runoff_left = self.arr.vol_runoff.data[i][j - 1]
            vol_runoff_leftdown = vol_runoff_down[j - 1]
            vol_runoff_rightup = vol_runoff_up[j + 1]
            vol_runoff_right = self.arr.vol_runoff.data[i][j + 1]
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
