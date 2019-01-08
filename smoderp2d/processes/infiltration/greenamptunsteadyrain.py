# TODO include also the surface retention as it is in Chu (1978)

import math
from scipy.optimize import newton

# option for stand alone testing of the class
if __name__ == "__main__":
    print '\n\n\n\ntest version of green-ampt infiltration\n\n\n\n'
    stand_alone = True
    BaseInfiltration = object
else:
    from smoderp2d.processes.infiltration import BaseInfiltration
    stand_alone = False


class SingleSoilGAIUR(object):
    """ Green ampt infiltration for unsteady rainfall for a single soil type

    based on S. T. Chu., Infiltration During an Unsteady Rain, 
    Water Resources Research,  vol. 14, no. 3, 1978
    """

    def __init__(self, ks, sm):
        """ for each soil type sets the variables 

        ks - saturated hydraulic conductivity
        sm - suction pressure at the wetting front (s) time difference of the moisture (m)
        """

        self._ks = 1e-5 
        self._sm = 1e-2

        # cumulative rainfall
        self._p_n_1 = self._p_n = 0.0
        # cumulative runoff
        self._r_n_1 = self._r_n = 0.0
        # cumulative infiltration
        self._f_n_1 = self._f_n = 0.0
        # previous time
        self._t_n_1 = 0.0

        self._ponded = False
        #self._beginning = True

        # only flobal variable
        # stores the infiltration height
        # for a given time step
        self.infiltration = 0.0

    def _indicator_u(self, i):
        """ indicating the ponding if the value is larger thant zero 

        C_u in Chu (1978)

        :param i: current precipitation intenzity
        """
        return self._p_n - self._r_n_1 - self._ks*self._sm/(i-self._ks)

    def _indicator_p(self):
        """ indicating the unponding if the value is larger thant zero 
        and the surface is ponded

        C_p in Chu (1978)
        """
        return self._p_n - self._f_n - self._r_n_1

    def _time_ponding(self, i):
        """ Calculates ponding time in a time interva
        where ponding is indicated.

        t_p in Chu (1978)

        :param i: current precipitation intenzity
        """
        return (self._ks*self._sm/(i-self._ks) - self._p_n_1 + self._r_n_1) / i + self._t_n_1

    def _prec_at_ponding(self, i, t_p):
        """ Calculates precipitatino at the ponding time.

        P(t_p) in Chu (1978)

        :param i: current precipitation intenzity
        """
        return self._p_n_1 + (t_p - self._t_n_1)*i

    def _pseudo_time(self, i, pt_p):
        """ Calculates preudo time. 

        This shift is a core of the Chu (1978) approach

        t_s in Chu (1978)

        :param i: current precipitation intenzity
        :param pt_p: precipitation at ponding time 
        """

        return ((pt_p - self._r_n_1)/self._sm - math.log(1.+(pt_p - self._r_n_1)/self._sm))*self._sm/self._ks

    def _shifted_time(self, t_s, t_p):
        """ Calculates shifted time. 

        This shifted time shifts the time in the green ampt.
        This shifted is a core of the Chu (1978) approach

        t_s in Chu (1978)

        :param t_s: time shift
        :param t_p: time of ponding 
        """

        return self._t_n - t_p + t_s

    def _greenampt_f(self, fn, T_shifted):
        """ green ampt formula 

        :param fn: cumulative infiltration
        :param T_shifted: shifted time 
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m) """

        return self._ks*T_shifted/self._sm - (fn/self._sm - math.log(1+fn/self._sm))

    def _cumulative_f(self, fn, T_shifted):
        """ Solve current cumulative infiltration ne newton's mehod 

        :param fn: cumulative infiltration
        :param T_shifted: shifted time 
        """

        # set variebls into green-ampt
        def ffp(fn): return self._greenampt_f(fn, T_shifted)

        # compute current cumulative infiltration
        return newton(ffp, self._ks*T_shifted)

    def _store_to_previous(self):
        """ Set new values into previous. """
        self._p_n_1 = self._p_n
        self._f_n_1 = self._f_n
        self._r_n_1 = self._r_n
        self._t_n_1 = self._t_n

    def _prt_vals(self):
        print '{:8.4f}  {:8.4f}  {:8.4f}  {:8.4f}'.format(
            self._t_n, self._p_n, self._f_n, self._r_n)

    def ga_unsteadyrain(self, cprec, t, dt):
        """ calculates next cumulative infiltration for a single soil type
        :param float sr: current rainfall height [m]
        :param t: current time 
        :param dt: current time step
        """

        # current precipitation intensity
        i = cprec/dt

        # add current precipitation height to cumulative precipitation
        self._p_n += cprec
        # new time
        self._t_n = t + dt

        # calculates indicator of unpunded to ponded
        Cu = self._indicator_u(i)
        # calculates indicator of punded to unponded

        if (not(self._ponded)):
            # TODO it condition shloud may be <=, check the literature
            if ((Cu < 0.0) | (self._ks >= i)):  # no ponding
                self._r_n = 0.0
                self._f_n = self._p_n - self._r_n
            else:
                self._ponded = True
                #self._beginning = False
                self._t_p = self._time_ponding(i)
                pt_p = self._prec_at_ponding(i, self._t_p)
                self._t_s = self._pseudo_time(i, pt_p)

        if (self._ponded):
            T_shifted = self._shifted_time(self._t_s, self._t_p)
            self._f_n = self._cumulative_f(self._f_n, T_shifted)
            Cp = self._indicator_p()
            if (Cp < 0.0):
                self._f_n = self._p_n - self._r_n_1
                self._ponded = False
            self._r_n = self._p_n - self._f_n

        if (stand_alone):
            self._prt_vals()

        # set infiltration for the time step
        self.infiltration = self._f_n - self._f_n_1
        # set new variables as old
        self._store_to_previous()


class GreenAmptInfiltrationUnsteadyRain(BaseInfiltration):

    def __init__(self, soils_data):
        """ make instance of SingleSoilGAIUR for each soil type 

        :param soils_data: combinat_index in the smoderp2d code
        """

        self._n = len(soils_data)
        self._soil = []
        for i in range(self._n):
            self._soil.append(SingleSoilGAIUR(
                ks=soils_data[i][1], sm=soils_data[i][2]))

    def precalc(self, dt, total_time, cprec):
        """ Precalculates potential infiltration got a given soil.

        :param cprec: current precipitation height
        """

        for i in range(self._n):
            self._soil[i].ga_unsteadyrain(cprec, total_time, dt)


# option for stand alone testing of the class
if __name__ == "__main__":

    # from Chu 1978
    sr = [[0., 0.], [7.167, 0.0206], [7.333, 0.0212], [7.417, 0.0244], [
        7.583, 0.0270], [7.667, 0.0308], [7.917, 0.0313], [8.000, 0.0346]]
    # sr = [[0., 0.], [0.083, 0.0013], [0.667, 0.0013],
    #[0.917, 0.0216], [1.167, 0.0221]]

    data = [[0, 2.777e-1, 2, 0], [0, 0.0142, 0.036, 0]]
    # from Chu 1978
    data = [[0, 0.0142, 0.036, 0]]
    t = GreenAmptInfiltrationUnsteadyRain([[0, 0.0142, 0.036, 0]])

    tt = 0
    for i in range(1, len(sr)):
        dt = sr[i][0] - sr[i-1][0]
        csr = sr[i][1] - sr[i-1][1]
        t.precalc(dt=dt, total_time=tt, cprec=csr)
        tt += dt
