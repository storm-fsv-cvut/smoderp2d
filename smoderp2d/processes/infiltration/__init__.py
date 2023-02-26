import numpy as np
import numpy.ma as ma
from smoderp2d.exceptions import NegativeWaterLevel

# combinatIndex muze byt tady jako globalni
# primenna, main loop bude pro infiltraci volat
# stejnou funkci, ale az taky bude jina globalni
# promenna nastavena. mene ifu v main loop
combinatIndex = []


def set_combinatIndex(newCombinatIndex):
    global combinatIndex
    combinatIndex = newCombinatIndex


def philip_infiltration(soil, bil):
    # print 'bil v infiltraci', bil
    for z in combinatIndex:
        if ma.any(soil == z[0]):
            if ma.all(bil < 0):
                raise NegativeWaterLevel()
            infiltration = z[3]

            bil = ma.where(infiltration > bil, 0, bil - infiltration)
            infiltration = ma.minimum(infiltration, bil)
    # print 'bil a inf v infiltraci\n', bil, infiltration
    return bil, infiltration


def phlilip(k, s, deltaT, totalT, NoDataValue):
    if k and s == NoDataValue:
        infiltration = NoDataValue
    # elif totalT == 0:
        # infiltration = k*deltaT  ## toto je chyba, infiltrace se rovna k az po ustaleni. Na zacatku je teoreticky nekonecno
    # else:
        # try:
    else:

        infiltration = (0.5 * s / ma.sqrt(totalT + deltaT) + k) * deltaT
        # except ValueError:
    # print k, s
    return infiltration
