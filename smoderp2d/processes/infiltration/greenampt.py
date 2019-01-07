from smoderp2d.core.general import GridGlobals
from smoderp2d.processes.infiltration import BaseInfiltration
from scipy.optimize import newton

import math


class GreenAmptInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex
        # TODO include into inputs should be different for different soils
        self._psi = 10./100.  # soil water potential at the wetting front
        # TODO include into inputs should be different for different soils
        self._d_theta = 0.4  # theta difference

    def _greenampt_F(self, F, k, t):
        """ Green-Ampt formula for cumulative infiltration 

        solution if found with Newton's method in optimization in _cumulative_F

        :param F: cumulative infiltration
        :param k: hydraulic conductivity
        :param t: t
        """
        return F - k*t + self._psi * self._d_theta * math.log(1 + F/(self._psi * self._d_theta))

    def _cumulative_F(self, k, t):
        """ Computes cumulative infiltration with Newton's method

        :param k: hydraulic conductivity
        :param t: t

        :return : cumulative infiltration in a given time
        """

        def FF(F): return self._greenampt_F(F, k, t)

        return newton(FF, k*t)

    def _greenampt_f(self, k, t, dt, NoDataValue):
        """ Computes infiltration rate 

        :param k: hydraulic conductivity
        :param t: time
        :param dt: time step

        :return : infiltration rate multiplied with time step
        """

        if k == NoDataValue:
            return NoDataValue
        else:
            F_t = self._cumulative_F(k, t)
            return k*((self._psi * self._d_theta)/F_t + 1)*dt

    def precalc(self, dt, total_time):
        """ Precalculates potential infiltration got a given soil.
        The precalculated value is storred in the self._combinat_index
        """

        NoDataValue = GridGlobals.get_no_data()

        for iii in self._combinat_index:
            k = iii[1]
            iii[3] = self._greenampt_f(
                k,
                dt,
                total_time,
                NoDataValue)
