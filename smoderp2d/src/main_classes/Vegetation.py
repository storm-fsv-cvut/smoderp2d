

import numpy as np

from smoderp2d.src.main_classes.General import Size
from smoderp2d.src.main_classes.General import Globals as Gl


class VegArrs:

    def __init__(self, veg_true, ppl, pi):
        self.veg_true = veg_true
        self.ppl = ppl
        self.pi = pi


# Documentation for a class.
#  More details.
#
class Vegetation(Size):

    # The constructor.

    def __init__(self):

        gl = Gl()
        r = gl.get_rows()
        c = gl.get_cols()
        mat_ppl = gl.get_mat_ppl()
        mat_pi = gl.get_mat_pi() / 1000.0
        self.n = 3
        self.arr = np.empty((r, c), dtype=object)

        for i in range(r):
            for j in range(c):
                self.arr[i][j] = VegArrs(0, mat_ppl[i][j], mat_pi[i][j])
