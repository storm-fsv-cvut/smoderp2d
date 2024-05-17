import numpy.ma as ma
import numpy as np


def shallowSurfaceKinematic(a, b, h_sheet):
    np.savetxt('mat_aa2.txt', a, fmt="%.2e")
    print('save mat aa 2')
    return ma.power(h_sheet, b) * a
