# @package smoderp2d.core.flow
#
#  Contains Classes and methods resolve
#  the flow type according the D8 or Mfda algorithm.
#
#  Flow algorithms itself  are stores in the package
#  smoderp2d.flow_algorithm.
#
#  Classes defined here assemble the
#  the algorithms and defines methods to
#  make D8 or mfda compatible within the SMODERP
#  framework.
#
#  Both classes can inherited by the
#  classes Kinematic or Diffuse in the
#  package smoderp2d.core.kinematic_diffuse
#


from smoderp2d.core.general import Globals

import smoderp2d.flow_algorithm.mfd as mfd
import smoderp2d.flow_algorithm.D8 as D8_
from smoderp2d.providers import Logger

# Defines methods for executing the one direction flow algorithm D8.
#
#  Can be inherited by the Classes:
#
#  - smoderp2d.core.kinematic_diffuse.Kinematic
#  - smoderp2d.core.kinematic_diffuse.Diffuse
#
class D8(object):

    # constructor
    #
    #  defines inflows list which defines the flow direction for each
    #  cell of the DEM. The kinematic approach is used the inflows are defines
    #  only once in this constructor.
    #

    def __init__(self):
        Logger.info("D8 flow algorithm")
        self.inflows = D8_.new_inflows(Globals.get_mat_fd())

    # updates #inflows list if the diffuse approach is used.
    #
    # In the diffusive approach the flow direction may change due to changes of the water level.
    #
    def update_inflows(self, fd):
        self.inflows = D8_.new_inflows(fd)

    # returns the water volume water flows into cell i , j from the previous time step based on the
    # inflows list, \n
    #
    # inflows list definition is shown in the method  new_inflows() in the package smoderp2d.flow_algorithm.D8
    #
    #  The total inflow is sum of sheet and rill runoff volume.
    #
    #  @return inflow_from_cells inflow volume from the adjacent cells
    #
    def cell_runoff(self, i, j):
        inflow_from_cells = 0.0
        for z in range(len(self.inflows[i][j])):
            ax = self.inflows[i][j][z][0]
            bx = self.inflows[i][j][z][1]
            iax = i + ax
            jbx = j + bx
            try:
                insurfflow_from_cell = self.arr[iax][jbx].V_runoff
            except:
                insurfflow_from_cell = 0.0
            try:
                inrillflow_from_cell = self.arr[iax][jbx].V_runoff_rill
            except:
                inrillflow_from_cell = 0.0
            inflow_from_cells = inflow_from_cells + \
                insurfflow_from_cell + inrillflow_from_cell

        return inflow_from_cells


# Defines methods for executing the multiple flow direction algorithm mfda.
#
#  Can be inherited by the Classes:
#
#  - smoderp2d.core.kinematic_diffuse.Kinematic
#  - smoderp2d.core.kinematic_diffuse.Diffuse
#
#  note: The rill flow, if computed, is always defined in terms
#  of one directions algorithm. In the class Mfda are therefore
#  defined rules for mfda which governs the sheet flow and D8
#  algorithm which defines the rill flow.
#
class Mfda(object):

    def __init__(self):

        Logger.info("Multiflow direction algorithm")
        self.inflows, fd_rill = mfd.new_mfda(
            mat_dmt, mat_nan, mat_fd, vpix, spix, rows, cols
        )
        self.inflowsRill = D8_.new_inflows(fd_rill)

    def update_inflows(self, fd):
        self.inflows, fd_rill = mfd.new_mfda(
            self.H, mat_nan, fd, vpix, spix, rows, cols)
        self.inflowsRill = D8_.new_inflows(fd_rill)

    def cell_runoff(self, i, j, sur=True):
        inflow_from_cells = \
            self.inflows[i - 1][j - 1][1] * \
            self.arr[i - 1][j - 1].V_runoff_pre + \
            self.inflows[i - 1][j][2] * \
            self.arr[i - 1][j].V_runoff_pre + \
            self.inflows[i - 1][j + 1][3] * \
            self.arr[i - 1][j + 1].V_runoff_pre + \
            self.inflows[i][j - 1][0] * self.arr[i][j - 1].V_runoff_pre + \
            self.inflows[i][j + 1][4] * self.arr[i][j + 1].V_runoff_pre + \
            self.inflows[i + 1][j - 1][7] * self.arr[i + 1][j - 1].V_runoff_pre + \
            self.inflows[i + 1][j][6] * self.arr[i + 1][j].V_runoff_pre + \
            self.inflows[i + 1][j + 1][5] * \
            self.arr[i + 1][j + 1].V_runoff_pre

        if Globals.isRill and sur:
            for z in range(len(self.inflowsRill[i][j])):
                ax = self.inflowsRill[i][j][z][0]
                bx = self.inflowsRill[i][j][z][1]
                iax = i + ax
                jbx = j + bx
                if self.arr[i][j].state == 1 or self.arr[i][j].state == 2: # rill
                    try:
                        inflow_from_cells += \
                            self.V_runoff_rill_pre[iax][jbx]  # toto jeste predelat u ryh
                    except:
                        inflow_from_cells += 0.0

        return inflow_from_cells
