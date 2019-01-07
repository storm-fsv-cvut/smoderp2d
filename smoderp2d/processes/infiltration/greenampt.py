from smoderp2d.core.general import GridGlobals
from smoderp2d.processes.infiltration import BaseInfiltration
from scipy.optimize import newton

import math


class SingleSoilGA(object):
    """ Green ampt infiltration for single soil type """

    def __init__(self, ks):
        """ for each soil type sets the variables 

        ks - saturated hydraulic conductivity
        """

        self._ks = ks
        
        # TODO include into inputs should be different for different soils
        self._psi = 0.01  # soil water potential at the wetting front
        # TODO include into inputs should be different for different soils
        self._d_theta = 0.4  # theta difference

        # only flobal variable
        # stores the infiltration height
        # for a given time step
        self.infiltration = 0.0

    def _greenampt_F(self, F, t):
        """ Green-Ampt formula for cumulative infiltration 

        solution if found with Newton's method in optimization in _cumulative_F

        :param F: cumulative infiltration
        :param t: t
        """
        return F - self._ks*t + self._psi * self._d_theta * math.log(1 + F/(self._psi * self._d_theta))

    def _cumulative_F(self, t):
        """ Computes cumulative infiltration with Newton's method

        :param t: t

        :return : cumulative infiltration in a given time
        """

        def FF(F): return self._greenampt_F(F, t)

        return newton(FF, self._ks*t)

    def greenampt_f(self, t, dt):
        """ Computes infiltration rate 

        :param t: time
        :param dt: time step
        """
        NoDataValue = GridGlobals.get_no_data()
        if (t == 0.0):
            self.infiltration = 1.e108
        else:
            if self._ks == NoDataValue:
                self.infiltration = NoDataValue
            else:
                F_t = self._cumulative_F(t)
                self.infiltration = self._ks * \
                    ((self._psi * self._d_theta)/F_t + 1.)


class GreenAmptInfiltration(BaseInfiltration):

    def __init__(self, soils_data):
        """ make instance of SingleSoilGA for each soil type 

        :param soils_data: combinat_index in the smoderp2d code
        """

        self._n = len(soils_data)
        self._soil = []
        for i in range(self._n):
            self._soil.append(SingleSoilGA(
                ks=soils_data[i][1]))

    def precalc(self, dt, total_time):
        """ Precalculates potential infiltration got a given soil.
        The precalculated value is storred in the self._combinat_index """

        for i in range(self._n):
            self._soil[i].greenampt_f(total_time, dt)
