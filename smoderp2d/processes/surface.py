import math


def shallowSurfaceKinematic(sur):

    a = sur.a
    b = sur.b
    h = sur.h_sheet_pre

    return math.pow(h, b) * a
