import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.core.flow import *
from smoderp2d.providers import Logger

import smoderp2d.flow_algorithm.flow_direction as flow_direction


def get_kinematic():
    class Kinematic(Mfda if Globals.mfda else D8):

        def __init__(self):
            Logger.info("Kinematic approach")
            super(Kinematic, self).__init__()

        def new_inflows(self):
            pass

        def update_H(self):
            pass

    return Kinematic


def get_diffuse():
    class Diffuse(Mfda if Globals.mfda else D8):

        def __init__(self):
            Logger.info("Diffuse approach")

            r = GridGlobals.r
            c = GridGlobals.c

            if r is None or c is None:
                exit("GridGlobal variables are not assigned")

            self.H = ma.masked_array(
                np.zeros([r, c], float), mask=GridGlobals.masks
            )

        def new_inflows(self):
            fd = flow_direction.flow_direction(
                self.arr.h_total_pre + Globals.mat_dem,
                self.rr,
                self.rc,
                self.pixel_area)
            self.update_inflows(fd)

        def update_H(self):

            arr = self.arr

            arr.H = arr.h + arr.z

            for i in self.rr:
                for j in self.rc[i]:
                    arr.slope = self.slope_(i, j)

    return  Diffuse
