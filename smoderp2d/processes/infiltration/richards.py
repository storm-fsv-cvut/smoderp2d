from smoderp2d.processes.infiltration import BaseInfiltration


class RichardsInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

        self._theta_r = 0.5
        self._theta_s = 0.12
        self._vg_alpha = 0.12
        self._vg_n = 2.5
        self._vg_m = 1-1/self._vg_n

        self._n = 20
        self._dx = 0.05

        self._n_soils = len(combinatIndex)
        self._soil = []

        # TODO create lists to store solutions
        # for i in range(self._n_soils):
        # self._soil.append()

    def _mualem_K(self, ks, h):
        """ Mualem Genuchten unsaturated hydraulic conductivity """
        a = self._vg_alpha
        n = self._vg_n
        m = self._vg_m

        if h >= 0:
            kr = 1
        else:
            kr = (1. - abs(a*h)**(n*m) * (1. + abs(a*h)**n)**(-m)) / \
                (1.+abs(a*h)**n)**(m/2)

        return kr*ks

    def _vg_theta(self, h):
        """ Van genuchten retention curve """

        a = self._vg_alpha
        n = self._vg_n
        m = self._vg_m
        tr = self._theta_r
        ts = self._theta_s

        if h >= 0:
            theta = ts
        else:
            theta = tr + (ts - tr) / \
                (1 + abs(a*h)**n)**m

        return theta

    def _dvg_theta_dh(self, h):
        """ First derivative of van genuchten retention curve, so called capilar capacity """

        a = self._vg_alpha
        n = self._vg_n
        m = self._vg_m
        tr = self._theta_r
        ts = self._theta_s

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
