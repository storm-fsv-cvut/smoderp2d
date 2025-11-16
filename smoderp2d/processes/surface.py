import numpy.ma as ma


def shallowSurfaceKinematic(a, b, h_sheet):
    #TODO JJ: check if a is zero... and call error if that is the case
    return ma.power(h_sheet, b) * a
