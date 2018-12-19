import math
from scipy.optimize import newton
try:
    from smoderp2d.processes.infiltration import BaseInfiltration
except ImportError:
    print '\n\n\n\ntest version of green-ampt infiltration\n\n\n\n'
    instance = True
    BaseInfiltration = object


class GreenAmptInfiltrationUnsteadyRain(BaseInfiltration):
    """ Green ampt infiltration for unsteady rainfall

    based on S. T. Chu., Infiltration During an Unsteady Rain, 
    Water Resources Research,  vol. 14, no. 3, 1978
    """

    def __init__(self, ks, sm):
        """ for each soil type sets the variables 

        ks - saturated hydraulic conductivity
        sm - suction pressure at the wetting front (s) time difference of the moisture (m)
        """

        self._ks = ks
        self._sm = sm

        # cumulative rainfall
        self._p_n_1 = self._p_n = 0.0
        # cumulative runoff
        self._r_n_1 = self._r_n = 0.0
        # cumulative infiltration
        self._f_n_1 = self._f_n = 0.0

    def _indicator(self, p_n, r_n_1, ks, sm, i):
        """ indicating the ponding if the value is larger thant zero 

        C_u in Chu (1978)

        :param p_n: current cumulative precipitation
        :param r_n_1: previous cumulative runoff 
        :param ks: saturated hydraulic conductivity
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m)
        :param i: current precipitation intenzity
        """

        return p_n - r_n_1 - k*sm/(i-k)

    def _time_ponding(self, p_n_1, r_n_1, ks, sm, i, t_n_1):
        """ returns time of ponding in current time step

        t_p in Chu (1978)

        :param p_n_1: previous cumulative precipitation
        :param r_n_1: previous cumulative runoff 
        :param ks: saturated hydraulic conductivity
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m)
        :param i: current precipitation intenzity
        :param t_n_1: previous time
        """

        return (ks*sm/(i-ks) - p_n_1 + r_n_1)/i + t_n_1

    def _pseudo_time(self, pt_p, r_n_1, k, sm, i):
        """ calculates preudo time 

        t_s in Chu (1978)

        :param p_n_1: precipitation at ponding time 
        :param r_n_1: previous cumulative runoff 
        :param ks: saturated hydraulic conductivity
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m)
        :param i: current precipitation intenzity
        :param t_n_1: previous time
        """

        return ((pt_p - r_n_1)/sm - math.log(1+(pt_p - r_n_1)/sm))*sm/k

    def _greenampt_f(self, fp, ks, t, sm):
        """ green ampt formula 


        :param fp: cumulative infiltration
        :param ks: saturated hydraulic conductivity
        :param t: time 
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m)
        """

        return ks*t/sm - (fp/sm - math.log(1+fp/sm))

    def _cumulative_f(self, fp, ks, t, sm):
        """ Solve current cumulative infiltration ne newton's mehod 

        :param fp: cumulative infiltration
        :param ks: saturated hydraulic conductivity
        :param t: time 
        :param sm: suction pressure at the wetting front (s) time difference of the moisture (m)
        """

        # set variebls into green-ampt
        def ffp(fp): return _greenampt_f(fp, ks, t, sm)

        # compute current cumulative infiltration
        return newton(ffp, ks*t)

    def calc_next(self, sr, t, dt):
        """ calculates next cumulative infiltration for a single soil type
        :param sr: current rainfall height 
        :param t: current time 
        :param dt: current time step
        """

        ponded = False

        n = len(sr)

        for i in range(1, n):
            I = (sr[i][1]-sr[i-1][1])/(sr[i][0]-sr[i-1][0])
            P_n = sr[i][1]

            if (I > K):
                if (not(ponded)):
                    Cu = indicator(P_n, R_n_1, K, SM, I)
                    if (Cu <= 0):
                        F_n = F_n_1 + sr[i][1] - R_n_1
                        R_n = R_n_1
                    else:
                        ponded = True
                if (ponded):
                    t_n = sr[i][0]
                    t_n_1 = sr[i-1][0]
                    t_p = time_ponding(P_n_1, R_n_1, K, SM, I, t_n_1)
                    Pt_p = P_n_1 + (t_p - t_n_1)*I
                    t_s = pseudo_time(Pt_p, R_n_1, K, SM, I)
                    T = t_n - t_p + t_s
                    F_n = _cumulative_F(F_n, K, T, SM)
                    R_n = P_n - F_n - 0.0

            else:
                F_n = F_n_1 + sr[i][1]
                R_n = R_n_1

            P_n_1 = P_n

        return 1


if __name__ == "__main__":

    sr = [[0., 0.], [7.167, 0.0206], [7.333, 0.0212], [7.417, 0.0244], [
        7.583, 0.0270], [7.667, 0.0308], [7.917, 0.0313], [8.000, 0.0346]]
    #sr = [[0.,0.],[0.083,0.0013],[0.667,0.0013],[0.917,0.0216],[1.167,0.0221]]

    t = GreenAmptInfiltrationUnsteadyRain([[0, 2.777e-1, 2, 0]])
