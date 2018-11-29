import math

from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger
from smoderp2d.core.general import Globals, GridGlobals

courantMax = 1.0
courantMin = 0.2


def update_hb(loc_V_to_rill, rillRatio, l, b):
    V = loc_V_to_rill
    if V < 0:
        raise SmoderpError()
    newb = math.sqrt(V / (rillRatio * l))
    if (V > 0):
        if newb > b:
            b = newb
            h = V / (b * l)
        else:
            h = V / (b * l)
    else:
        h = b = 0.0

    return h, b


def rill(i, j, sur):
    """ calculates discharge from rill

    :param sur: element of a surface array

    :return: discharge from cell in in m3/s
    :return: rill flow velocity in in m/s
    """

    h_rill_pre = sur.h_rill_pre
    slope = Globals.get_slope(i, j)
    rillratio = 0.7
    b = sur.rill_width
    l = Globals.get_efect_vrst(i, j)
    n = Globals.get_n(i, j)

    V_to_rill = h_rill_pre * GridGlobals.pixel_area
    h, b = update_hb(V_to_rill, rillratio, l, b)
    if b == 0 : return 0.0, 0.0
    R_rill = (h * b) / (b + 2 * h)
    v = math.pow(
        R_rill,
        (2.0 / 3.0)) * 1 / n * math.pow(slope / 100,
                                        0.5)  # m/s
    q = v * rillratio * b * b  # [m3/s]
    
    sur.rill_width = b
    
    return [q, v]
