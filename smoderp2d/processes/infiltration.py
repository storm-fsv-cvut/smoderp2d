import numpy as np
import math
import tensorflow as tf
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
    infiltration = zeros = tf.Variable(
        [[0] * soil.shape[1]] * soil.shape[0], dtype=tf.float32)

    for z in combinatIndex:
        cond = tf.equal(soil,
                    tf.Variable([[z[0]] * soil.shape[1]] * soil.shape[0],
                        dtype=tf.float32))

        infiltration_a = infiltration = tf.Variable(
            [[z[3]] * soil.shape[1]] * soil.shape[0], dtype=tf.float32)
        # TODO: if bil < 0: raise NegativeWaterLevel()
        cond_in = infiltration_a > bil
        infiltration_in = tf.where(cond_in, bil, infiltration)
        infiltration = tf.where(cond, infiltration_in, infiltration)
        bil_in = tf.where(cond_in, zeros, bil - infiltration)
        bil = tf.where(cond, bil_in, bil)

    return bil, infiltration


def phlilip(k, s, deltaT, totalT, NoDataValue):
    if k and s == NoDataValue:
        infiltration = NoDataValue
    # elif totalT == 0:
        # infiltration = k*deltaT  ## toto je chyba, infiltrace se rovna k az po ustaleni. Na zacatku je teoreticky nekonecno
    # else:
        # try:
    else:

        infiltration = (0.5 * s / math.sqrt(totalT + deltaT) + k) * deltaT
        # except ValueError:
    # print k, s
    return infiltration
