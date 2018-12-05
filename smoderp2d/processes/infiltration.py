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
class BaseInfiltration(object):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex
        
    def _philip(self,k, s, deltaT, totalT, NoDataValue):
        """ pilips formula """
        if k and s == NoDataValue:
            infiltration = NoDataValue
        else:
            infiltration = (0.5 * s / math.sqrt(totalT + deltaT) + k) * deltaT
        return infiltration
    

    def precalc(self, dt, total_time):
        """ Precalculates potential infiltration got a given soil.
        The precalculated value is storred in the self._combinat_index
        """

        NoDataValue = GridGlobals.get_no_data()

        for iii in self._combinat_index:
            index = iii[0]
            k = iii[1]
            s = iii[2]
            iii[3] = self._philip(
                k,
                s,
                dt,
                total_time,
                NoDataValue)

    def current_infiltration(self, soil, bil):
        """ Returns the actual infiltrated water height 

        :param soil: soil type in current cell
        :param bil: current water level
        """
        for z in self._combinat_index:
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


class GreenAmptInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

    def precalc(self, dt, total_time):
        raise NotImplemented("Not implemented for Green Ampt infiltration")

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Green Ampt infiltration")


class RichardsInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

    def precalc(self, dt, total_time):
        raise NotImplemented("Not implemented for Richards infiltration")

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Richards infiltration")
