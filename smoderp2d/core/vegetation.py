"""TODO."""

import numpy as np
import tensorflow as tf

from smoderp2d.core.general import GridGlobals, DataGlobals, Size, Globals

class VegArrs(object):
    """Vegetation attributes."""

    veg = tf.Variable([[False] * GridGlobals.c] * GridGlobals.r, dtype=tf.int32)
    ppl = DataGlobals.get_mat_ppl_tf()
    pi = tf.Variable(Globals.get_mat_pi() / 1000.0)
    veg_true = tf.Variable([[0] * GridGlobals.c] * GridGlobals.r)


class Vegetation(GridGlobals, Size, VegArrs):
    def __init__(self):
        """TODO."""
        self.dims = 0
        super(Vegetation, self).__init__()

        self.n = 3 # TODO ?
