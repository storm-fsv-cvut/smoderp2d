"""TODO."""

import numpy.ma as ma

from smoderp2d.core.general import GridGlobals, DataGlobals, Globals
from smoderp2d.core.surface import SurArrs


class VegArrs(object):
    def __init__(self, veg, ppl, pi):
        """Vegetation attributes.

        :param veg bool: True for vegetation
        :param ppl: pomerna plocha listova (leave area index)
        :param pi: potential interception
        """
        self.veg = veg
        self.ppl = ma.masked_array(ppl, mask=GridGlobals.masks)
        self.pi = ma.masked_array(pi, mask=GridGlobals.masks)


class Vegetation(GridGlobals):
    def __init__(self):
        """Class stores info about the vegetation cover."""
        super(Vegetation, self).__init__()

        self.arr.set_outsides(SurArrs)

        # TODO move this conversion into data preparation
        mat_pi = Globals.get_mat_pi() / 1000.0  # convert unit mm -> m

        self.arr = VegArrs(False, DataGlobals.get_mat_ppl(), mat_pi)
