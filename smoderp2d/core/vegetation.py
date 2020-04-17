"""TODO."""

import numpy as np

from smoderp2d.core.general import GridGlobals, DataGlobals, Size, Globals

class VegArrs(object):
    def __init__(self, veg, ppl, pi):
        """Vegetation attributes.

        :param veg bool: True for vegetation
        :param ppl: pomerna plocha listova (leave area index)
        :param pi: potential interception
        """
        self.veg = veg
        self.ppl = ppl
        self.pi = pi

class Vegetation(GridGlobals, Size):
    def __init__(self):
        """Class stores info about the vegetation cover."""
        super(Vegetation, self).__init__()
        
        # convert unit mm -> m 
        # TODO move this conversion into data preparation
        mat_pi = Globals.get_mat_pi() / 1000.0

        # number of variabes (used in class Size)
        self.n = 3

        for i in range(self.r):
            for j in range(self.c):
                self.arr[i][j] = VegArrs(False,
                                         DataGlobals.get_mat_ppl(i, j),
                                         mat_pi[i][j]
                )
