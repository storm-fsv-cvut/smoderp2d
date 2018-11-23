import math


def shallowSurfaceKinematic(sur):

    a = sur.a
    b = sur.b
    h = sur.h_sheet_old
    
    return math.pow(h, b) * a
