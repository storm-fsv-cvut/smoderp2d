import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.core.flow import *
from smoderp2d.providers import Logger

import smoderp2d.flow_algorithm.flow_direction as flow_direction

class Kinematic(Mfda if Globals.mfda else D8):

    def __init__(self):
        Logger.info("Kinematic approach")
        super(Kinematic, self).__init__()

    def new_inflows(self):
        pass

    def update_H(self):
        pass


class Diffuse(Mfda if Globals.mfda else D8):

    def __init__(self):
        Logger.info("Diffuse approach")
        if (Globals.r is None or Globals.r is None):
            exit("Global variables are not assigned")

        masks = [[True] * GridGlobals.c for _ in range(GridGlobals.r)]
        rr, rc = GridGlobals.get_region_dim()
        for r_c_index in range(len(rr)):
            for c in rc[r_c_index]:
                masks[rr[r_c_index]][c] = False

        r = Globals.r
        c = Globals.c

        self.H = ma.masked_array(np.zeros([r, c], float), mask=masks)

    def new_inflows(self):
        fd = flow_direction.flow_direction(
            self.H,
            self.rr,
            self.rc,
            self.br,
            self.bc,
            self.pixel_area)
        self.update_inflows(fd)

    def update_H(self):

        arr = self.arr

        for i in self.rr:
            for j in self.rc[i]:
                arr.H[i][j] = arr.h[i][j] + arr.z[i][j]

        for i in self.rr:
            for j in self.rc[i]:
                arr.slope = self.slope_(i, j)
