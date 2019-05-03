"""TODO."""

import numpy as np

from smoderp2d.core.general import GridGlobals, DataGlobals, Size, Globals

class VegArrs(object):
    def __init__(self, veg, ppl, pi):
        """Vegetation attributes.

        :param veg bool: True for vegetation
        :param ppl: TODO
        :param pi: TODO
        """
        self.veg = veg
        self.ppl = ppl
        self.pi = pi

class Vegetation(GridGlobals, Size):
    def __init__(self):
        """TODO."""
        self.dims = 27
        super(Vegetation, self).__init__()
        
        mat_pi = Globals.get_mat_pi() / 1000.0

        self.n = 3 # TODO ?

        arr_np = np.array(self.arr.numpy(), dtype=np.float64)

        for i in range(self.r):
            for j in range(self.c):
                arr_np[i, j, 24] = False
                arr_np[i, j, 25] = DataGlobals.get_mat_ppl(i, j)
                arr_np[i, j, 26] = mat_pi[i][j]

        self.arr.assign(arr_np)
