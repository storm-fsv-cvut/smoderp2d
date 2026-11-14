import numpy as np
import numpy.ma as ma
from smoderp2d.core.general import Globals
# from smoderp2d.exceptions import NegativeWaterLevel

# combinatIndex muze byt tady jako globalni
# primenna, main loop bude pro infiltraci volat
# stejnou funkci, ale az taky bude jina globalni
# promenna nastavena. mene ifu v main loop
combinatIndex = []

# set error level of numpy float underflow only to warning instead of errors
np.seterr(under='warn')


def set_combinatIndex(newCombinatIndex):
    global combinatIndex
    combinatIndex = newCombinatIndex


def philip_infiltration(soil, bil):
    infiltration = combinatIndex[0][3]
    for z in combinatIndex:
        # if ma.all(bil < 0):
        #     raise NegativeWaterLevel()

        infilt_bil_cond = z[3] > bil

        if Globals.computationType == 'explicit':
            infiltration = ma.where(
                soil == z[0],
                ma.where(infilt_bil_cond, bil, z[3]),
                infiltration
            )
            
            bil = ma.where(
                soil == z[0],
                ma.where(infilt_bil_cond, 0, bil - z[3]),
                bil
            )
        else:
            infiltration = ma.where(
                soil == z[0],
                ma.where(infilt_bil_cond, bil, z[3]),
                infiltration
            )

    return bil, infiltration


def philip(k, s, deltaT, totalT, NoDataValue):
    if k and s == NoDataValue:
        infiltration = NoDataValue
    else:
        infiltration1 = ma.where(
            totalT == 0,
            s * 0.0000001 ** 0.5 + k * 0.0000001,
            s * totalT ** 0.5 + k * totalT
        )
        infiltration2 = s * (totalT + deltaT)**0.5 + k * (totalT + deltaT)
        
        infiltration = infiltration2 - infiltration1

        # except ValueError:
    return infiltration
