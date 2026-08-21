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
    # step 2e: soil (surface.arr.soil_type) and bil may still be
    # numpy.ma at the call boundary - read raw .data via np.asarray()
    # up front. soil holds category ids built by
    # providers/base/data_preparation.py:_get_inf_combinat_index(),
    # which assigns each unique (k, s) combination a unique sequential
    # index 0..len(combinatIndex)-1 and gives every cell in the raster
    # (including NoData/boundary cells) exactly one such id - the
    # categories are disjoint by construction, so the previous
    # sequential "for z in combinatIndex: ma.where(soil == z[0], ...,
    # <accumulator>)" loop only ever wrote each cell once, in whichever
    # iteration matched its own category. That makes it equivalent to
    # a single vectorized lookup indexed directly by category id,
    # without the loop and without the per-iteration ma.where nesting.
    soil_idx = np.asarray(soil).astype(np.intp)
    bil = np.asarray(bil)

    cap = np.empty(len(combinatIndex))
    for z in combinatIndex:
        cap[z[0]] = z[3]
    cap_cell = cap[soil_idx]

    infilt_bil_cond = cap_cell > bil

    if Globals.computationType == 'explicit':
        infiltration = np.where(infilt_bil_cond, bil, cap_cell)
        bil = np.where(infilt_bil_cond, 0, bil - cap_cell)
    else:
        infiltration = np.where(infilt_bil_cond, bil, cap_cell)

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
