import numpy as np
import math
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
    for z in combinatIndex:
        if soil == z[0]:
            infiltration = z[3]
            if bil < 0:
                raise NegativeWaterLevel()
            if infiltration > bil:
                infiltration = bil
                bil = 0
            else:
                bil = bil - infiltration
    return bil, infiltration


def phlilip(k, s, deltaT, totalT, NoDataValue):
    if k and s == NoDataValue:
        infiltration = NoDataValue
    else:

        infiltration = (0.5 * s / math.sqrt(totalT + deltaT) + k) * deltaT
    return infiltration
