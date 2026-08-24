import numpy as np

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger

courantMax = 1.0


def update_hb(loc_V_to_rill, rillRatio, l, b):
    # numpy.ma removal: loc_V_to_rill is already a plain ndarray,
    # b (= SurArrs.rillWidth) is still numpy.ma, and l
    # (= Globals.mat_effect_cont) is plain. The raw .data is read once
    # through np.asarray() so that the whole function body below is plain
    # ndarray arithmetic - the operations and their order are unchanged.
    V = np.asarray(loc_V_to_rill)
    b = np.asarray(b)
    l = np.asarray(l)

    if Globals.computationType == 'explicit':
        # CAREFUL: this is a reduction over the whole grid, not an
        # elementwise operation. The original ma.any() on a MaskedArray
        # ignored invalid cells; on a plain ndarray it would take them
        # into account, and their underlying value can be anything (no
        # one computes out-of-domain cells). The test is therefore
        # restricted to GridGlobals.valid_idx, i.e. exactly the set of
        # cells the mask would have exposed.
        valid_idx = GridGlobals.valid_idx
        if valid_idx is None:
            neg = V < 0
        else:
            neg = V.ravel()[valid_idx] < 0
        if np.any(neg):
            raise SmoderpError('V is smaller than 0')
        cond = V > 0
    else:
        cond = V >= 0

    with np.errstate(divide='ignore', invalid='ignore'):
        newb_arg = V / (rillRatio * l)
    # ma.sqrt() masked a negative argument, np.sqrt() would give nan plus
    # a RuntimeWarning. The result is discarded either way (wherever the
    # argument is negative, cond is necessarily False), so the argument is
    # merely clipped at zero from below.
    newb = np.sqrt(np.where(newb_arg > 0, newb_arg, 0))
    b = np.where(cond, np.maximum(b, newb), b)

    denom = b * l
    with np.errstate(divide='ignore', invalid='ignore'):
        h = V / denom
    # ma.divide() masked cells with a zero denominator and put the
    # numerator back into .data (_DomainedBinaryOperation behaviour). The
    # same thing is reproduced here so that no nan/inf is left in the
    # array - otherwise the value is identical cell by cell.
    h = np.where(np.isfinite(h), h, V)

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
