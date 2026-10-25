import numpy.ma as ma


def shallowSurfaceKinematic(a, b, h_sheet):
    return ma.power(h_sheet, b) * a
