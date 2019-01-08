import numpy as np
import math
from smoderp2d.exceptions import NegativeWaterLevel
from smoderp2d.core.general import Globals, GridGlobals


# combinatIndex muze byt tady jako globalni
# primenna, main loop bude pro infiltraci volat
# stejnou funkci, ale az taky bude jina globalni
# promenna nastavena. mene ifu v main loop
combinatIndex = []


def set_combinatIndex(newCombinatIndex):
    global combinatIndex
    combinatIndex = newCombinatIndex


# base infiltration is philips infiltration
class SingleSoilBI(object):
    """ infiltration for single soil class """

    def __init__(self, ks, s):

        # saturated hydraulic conductivity
        self._ks = ks
        self._ks = 1e-5
        # sorbtion
        self._s = 5e-5
        # only flobal variable
        # stores the infiltration height
        # for a given time step
        self.infiltration = 0

    def philip(self, deltaT, totalT):
        """ pilips formula """

        NoDataValue = GridGlobals.get_no_data()

        if self._ks and self._s == NoDataValue:
            self.infiltration = NoDataValue
        else:
            self.infiltration = (
                0.5 * self._s / math.sqrt(totalT + deltaT) + self._ks) * deltaT


class BaseInfiltration(object):

    def __init__(self, soils_data):
        """ make instances of SingleSoilBI for each soil type 

        :param soils_data: combinat_index in the smoderp2d code
        """

        self._n = len(soils_data)
        self._soil = []
        for i in range(self._n):
            self._soil.append(SingleSoilBI(
                ks=soils_data[i][1], s=soils_data[i][2]))

    def precalc(self, dt, total_time, cprec):
        """ Precalculates potential infiltration got a given soil.
        The precalculated value is storred in the self._combinat_index
        """

        for i in range(self._n):
            self._soil[i].philip(dt, total_time)

    def current_infiltration(self, soil_id, bil):
        """ Returns the actual infiltrated water height 

        :param soil_id: soil type in current cell
        :param bil: current water level
        """

        infiltration = self._soil[soil_id].infiltration
        if bil < 0:
            raise NegativeWaterLevel()
        if infiltration > bil:
            infiltration = bil
            bil = 0
        else:
            bil = bil - infiltration

        return bil, infiltration
