"""TODO."""

import numpy as np

from smoderp2d.core.general import Size, Globals

class VegArrs(object):
    def __init__(self, veg_true, ppl, pi):
        """Vegetation attributes.

        :param veg_true: True for vegetation
        :param ppl:
        :param pi:
        """
        self.veg_true = veg_true
        self.ppl = ppl
        self.pi = pi

class Vegetation(Size):
    def __init__(self):
        """TODO."""
        r = Globals.get_rows()
        c = Globals.get_cols()
        mat_ppl = Globals.get_mat_ppl()
        mat_pi = Globals.get_mat_pi() / 1000.0

        self.n = 3 # TODO
        self.arr = np.empty((r, c), dtype=object)

        for i in range(r):
            for j in range(c):
                self.arr[i][j] = VegArrs(False, mat_ppl[i][j], mat_pi[i][j])
