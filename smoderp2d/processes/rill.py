import numpy.ma as ma

from smoderp2d.core.general import Globals
from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger

courantMax = 1.0


def update_hb(loc_V_to_rill, rillRatio, l, b):
    V = loc_V_to_rill
    if Globals.computationType == 'explicit':
        if ma.any(V < 0):
            raise SmoderpError('V is smaller than 0')
        cond = V > 0
    else:
        cond = V >= 0
    newb = ma.sqrt(V / (rillRatio * l))
    b = ma.where(
        cond,
        ma.maximum(b, newb),
        b
    )
    h = V / (b * l)

    return h, b


def rill(V_to_rill, rillRatio, l, b, delta_t, n, slope):
    V_rill_runoff = 0
    V_rill_rest = 0     # vrillrest z predchoziho kroku je zapocten v vtorill
    # b = 0.0

    v = [0]
    q = [0]

    # for k in range(ratio):

    #     h, b = update_hb(
    #         loc_V_to_rill + V_rill_rest, rillRatio, l, b)

    #     R_rill = (h * b) / (b + 2 * h)
    #     v[k] = ma.pow(
    #         R_rill,
    #         (2.0 / 3.0)) * 1 / n * ma.pow(slope / 100, 0.5)  # m/s

    #     q[k] = v[k] * rillRatio * b * b  # [m3/s]
    #     V = q[k] * loc_delta_t
    #     courant = v[k] / 0.5601 * loc_delta_t / l

    #     if courant <= courantMax:

    #         if V > (loc_V_to_rill + V_rill_rest):
    #             V_rill_rest = 0
    #             V_rill_runoff = V_rill_runoff + loc_V_to_rill + V_rill_rest

    #         else:
    #             V_rill_rest = loc_V_to_rill + V_rill_rest - V
    #             V_rill_runoff = V_rill_runoff + V

    #     else:
    #         return b, V_rill_runoff, V_rill_rest, q, v, courant

    return b, V_rill_runoff, V_rill_rest, q, v, courant


# Method calculates rill flow and the rill size
#
#  @param h_rill  water level in the rill
#  @param V_rill_rest water volume from the previous time step
#  @param rillSize volume of the existing rill
#  @param pixelArea area of a computational pixel
#  @param rillRatio rill heght rill width ratio \f$ rillRatio =\frac{y}{b} \f$
#  @param l rill length
#  @param n roughness of the rill
#  @param slope slope of the computational cell
#  @param delta_t  time step
#
#
#  \image html rill_schema.png "The rill shape and dimension" width=5cm
#
#  First the function calculates the inflow from the adjecent cells together
#  with the water volume from the previous time step \n
#  \f$ V_{to\ rill} = h_{rill} \ pixelArea + V_{rill\ rest} \f$
#
#
#  Next step is to chech weather or not is the rill large enough to capture
#  the volume of the water \n
#  \b if \f$V_{to\ rill}\f$ > \f$V_{rill}\f$ \n
#    \f$ V_{rill} = y^{2} \ rillRatio \ length \f$ \n
#  \n
#
#
#
# def rillCalculations(sur, pixelArea, l, rillRatio, n, slope, delta_t):
#
#     input()
#     h_rill = sur.h_rill
#     b = sur.rillWidth
#     V_to_rill = h_rill * pixelArea
#     sur.V_to_rill = V_to_rill
#
#     b_tmp = b
#     courant = courantMax + 1.0
#
#     while courant > courantMax:
#
#         b = b_tmp
#         # if sur.state != 2 :
#         #     b = 0
#
#         b, V_rill_runoff, V_rill_rest, q, v, courant = rill(
#             V_to_rill, rillRatio, l, b, delta_t, n, slope
#         )
#         # if ppp :
#         if courant > courantMax:
#             Logger.debug('------ ratio += 1 -----')
#             input()
#             ratio += 1
#             if ratio > 10:
#                 return (
#                     b_tmp, V_to_rill, V_rill_runoff, V_rill_rest, 0.0, 0.0,
#                     11, courant
#                 )
#
#     qMax = max(q)
#     vMax = max(v)
#     return b, V_to_rill, V_rill_runoff, V_rill_rest, qMax, vMax, ratio, courant
