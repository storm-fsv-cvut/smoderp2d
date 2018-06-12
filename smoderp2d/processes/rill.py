import math

from smoderp2d.exceptions import SmoderpError
from smoderp2d.providers import Logger

courantMax = 1.0
courantMin = 0.2

def update_hb(loc_V_to_rill, rillRatio, l, b, ratio, ppp=False):
    V = loc_V_to_rill
    if V < 0:
        raise SmoderpError()
    newb = math.sqrt(V / (rillRatio * l))
    # if ppp :  print 'zvetsuje', newb, b, V
    if (V > 0):
        if newb > b:
            b = newb
            h = V / (b * l)
        else:
            h = V / (b * l)
    else:
        h = V / (b * l)

    return h, b


def rill(V_to_rill, rillRatio, l, b, delta_t,
         ratio, n, slope, pixelArea, ppp=False):

    V_rill_runoff = 0
    V_rill_rest = 0     # vrillrest z predchoziho kroku je zapocten v vtorill
    # b = 0.0

    loc_delta_t = delta_t / ratio
    loc_V_to_rill = V_to_rill / ratio

    v = [0] * ratio
    q = [0] * ratio

    for k in range(ratio):

        h, b = update_hb(
            loc_V_to_rill + V_rill_rest, rillRatio, l, b, ratio, ppp)

        R_rill = (h * b) / (b + 2 * h)
        v[k] = math.pow(
            R_rill,
            (2.0 / 3.0)) * 1 / n * math.pow(slope / 100,
                                            0.5)  # m/s

        q[k] = v[k] * rillRatio * b * b  # [m3/s]
        V = q[k] * loc_delta_t
        courant = v[k] / 0.5601 * loc_delta_t / l

        if (courant <= courantMax):

            if V > (loc_V_to_rill + V_rill_rest):
                V_rill_rest = 0
                V_rill_runoff = V_rill_runoff + loc_V_to_rill + V_rill_rest

            else:
                V_rill_rest = loc_V_to_rill + V_rill_rest - V
                V_rill_runoff = V_rill_runoff + V

        else:
            return b, V_rill_runoff, V_rill_rest, q, v, courant

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
#  @param ratio  ratio to make the time division to satisfy the the courant condition
#
#
#  \image html rill_schema.png "The rill shape and dimension" width=5cm
#
#  First the function calculates the inflow from the adjecent cells together with the water volume from the previous time step \n
#  \f$ V_{to\ rill} = h_{rill} \ pixelArea + V_{rill\ rest} \f$
#
#
#  Next step is to chech weather or not is the rill large enough to caputre the volume of the water \n
#  \b if \f$V_{to\ rill}\f$ > \f$V_{rill}\f$ \n
#    \f$ V_{rill} = y^{2} \ rillRatio \ length \f$ \n
#  \n
#
#
#
def rillCalculations(
        sur, pixelArea, l, rillRatio, n, slope, delta_t, ratio, ppp=False):

    raw_input()
    h_rill = sur.h_rill
    b = sur.rillWidth
    V_to_rill = h_rill * pixelArea
    sur.V_to_rill = V_to_rill

    b_tmp = b
    courant = courantMax + 1.0

    while (courant > courantMax):

        b = b_tmp
        # if sur.state != 2 :
            # b = 0

        # print '\t', b,
        b, V_rill_runoff, V_rill_rest, q, v, courant = rill(
            V_to_rill, rillRatio, l, b, delta_t, ratio, n, slope, pixelArea, ppp)
        # if ppp :
        ### print '\t', b, V_rill_runoff, V_rill_rest, courant
        if (courant > courantMax):
            Logger.debug('------ ratio += 1 -----')
            raw_input()
            ratio += 1
            if (ratio > 10):
                return b_tmp, V_to_rill, V_rill_runoff, V_rill_rest, 0.0, 0.0, 11, courant

    qMax = max(q)
    vMax = max(v)
    # print raw_input('..')
    # print "V_to_rill, V_rill_runoff", V_to_rill, V_rill_runoff
    return b, V_to_rill, V_rill_runoff, V_rill_rest, qMax, vMax, ratio, courant
