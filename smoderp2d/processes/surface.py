import numpy as np


def shallowSurfaceKinematic(sur):

    a = sur.a
    b = sur.b
    h = sur.h_sheet

    return np.power(h, b) * a
