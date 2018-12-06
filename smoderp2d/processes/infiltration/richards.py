try:
    from smoderp2d.processes.infiltration import BaseInfiltration
except ImportError:
    print 'test version of richards infiltration'
    instance = True
    BaseInfiltration = object

import numpy as np


class SoilProfile():

    def __init__(self, n, dx, tr, ts, vg_a, vg_n, ks):
        """ Store parameters which are soil profile specific. 

        :param int n: number of nodes for discretiataion
        :param real dx: spatial step of discretiataion
        """

        self.theta_r = tr
        self.theta_s = ts
        self.vg_alpha = vg_a
        self.vg_n = vg_n
        self.vg_m = 1-1/self.vg_n

        # t-1 solution with dirichlet boundary condition
        self.dir_pre = np.zeros([n], float)
        # t   solution with dirichlet boundary condition
        self.dir_new = np.zeros([n], float)

        # t-1 solution with neumann boundary condition
        self.neu_pre = np.zeros([n], float)
        # t   solution with neumann boundary condition
        self.neu_new = np.zeros([n], float)


class RichardsInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

        self._n = 20
        self._dx = 0.05

        self._n_soils = len(combinatIndex)

        # this list of soil profile instances
        # should in terms of indices correspond
        # to id in combinatIndex array
        self._soil = []

        for i in range(self._n_soils):
            print i
            self._soil.append(SoilProfile(n=self._n, dx=self._dx, tr=0.2,
                                          ts=0.5, vg_a=0.01, vg_n=2.5, ks=self._combinat_index[i][1]))

    def _mualem_K(self, sp, h):
        """ Mualem Genuchten unsaturated hydraulic conductivity 

        :param sp: instance of SoilProfile class
        """
        a = sp.vg_alpha
        n = sp.vg_n
        m = sp.vg_m

        if h >= 0:
            kr = 1
        else:
            kr = (1. - abs(a*h)**(n*m) * (1. + abs(a*h)**n)**(-m)) / \
                (1.+abs(a*h)**n)**(m/2)

        return kr*ks

    def _vg_theta(self, sp, h):
        """ Van genuchten retention curve 

        :param sp: instance of SoilProfile class
        """

        a = sp.vg_alpha
        n = sp.vg_n
        m = sp.vg_m
        tr = sp.theta_r
        ts = sp.theta_s

        if h >= 0:
            theta = ts
        else:
            theta = tr + (ts - tr) / \
                (1 + abs(a*h)**n)**m

        return theta

    def _dvg_theta_dh(self, sp, h):
        """ First derivative of van genuchten retention curve, so called capilar capacity """

        a = sp.vg_alpha
        n = sp.vg_n
        m = sp.vg_m
        tr = sp.theta_r
        ts = sp.theta_s

        if h >= 0:
            # TODO consider to use specific storativity
            C = 0
        else:
            C = a*m*n*(-tr + ts)*(-(a*h))**(-1. + n) * \
                (1. + (-(a*h))**n)**(-1. - m)

        return C

    def precalc(self, dt, total_time):
        raise NotImplemented("Not implemented for Richards infiltration")

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Richards infiltration")


if instance:
    t = RichardsInfiltration([[0, 0.3, 2, 0], [1, 0.4, 2, 0]])
