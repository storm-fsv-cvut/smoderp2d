"""TODO."""

import numpy as np

from smoderp2d.core.general import GridGlobals, DataGlobals, Globals
from smoderp2d.core.surface import SurArrs


class VegArrs(object):
    def __init__(self, veg, ppl, pi):
        """Vegetation attributes.

        :param veg bool: True for vegetation
        :param ppl: pomerna plocha listova (leave area index)
        :param pi: potential interception
        """
        # numpy.ma removal: measured - the mask on these two was always
        # exactly GridGlobals.masks, never anything more, and both are
        # constant for the whole run. Note that pi carries the no-data
        # value through the mm -> m conversion below, so outside the
        # computation area it holds -9.999 rather than -9999; nothing keys
        # off that value, the area is defined by GridGlobals.valid.
        self.veg = veg
        self.ppl = np.asarray(ppl)
        self.pi = np.asarray(pi)


class Vegetation(GridGlobals):
    def __init__(self):
        """Class stores info about the vegetation cover."""
        super(Vegetation, self).__init__()

        self.arr.set_outsides(SurArrs)

        # TODO move this conversion into data preparation
        mat_pi = Globals.get_mat_pi() / 1000.0  # convert unit mm -> m

        self.arr = VegArrs(False, DataGlobals.get_mat_ppl(), mat_pi)
