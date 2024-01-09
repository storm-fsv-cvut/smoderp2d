import numpy.ma as ma


def shallowSurfaceKinematic(a, b, h_sheet):
    a = 160
    return ma.power(h_sheet, b) * a
