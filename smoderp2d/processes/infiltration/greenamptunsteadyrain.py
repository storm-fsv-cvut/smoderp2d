import math
from scipy.optimize import newton
try:
    from smoderp2d.processes.infiltration import BaseInfiltration
except ImportError:
    print '\n\n\n\ntest version of green-ampt infiltration\n\n\n\n'
    instance = True
    BaseInfiltration = object


class GreenAmptInfiltrationUnsteadyRain(BaseInfiltration):
    """ Green ampt infiltariont for unsteady rainfall

    based on S. T. Chu., Infiltration During an Unsteady Rain, 
    Water Resources Research,  vol. 14, no. 3, 1978
    """

    def indicator(self, P_n, R_n_1, K, SM, I):
        return P_n - R_n_1 - K*SM/(I-K)

    def time_ponding(self, P_n_1, R_n_1, K, SM, I, t_n_1):
        return (K*SM/(I-K) - P_n_1 + R_n_1)/I + t_n_1

    def pseudo_time(self, Pt_p, R_n_1, K, SM, I):
        return ((Pt_p - R_n_1)/SM - math.log(1+(Pt_p - R_n_1)/SM))*SM/K

    def _greenampt_F(self, Fp, K, T, SM):

        return K*T/SM - (Fp/SM - math.log(1+Fp/SM))

    def _cumulative_F(self, Fp, K, T, SM):

        def FFp(Fp): return _greenampt_F(Fp, K, T, SM)

        return newton(FFp, K*T)

    def main(self, sr):

        K = 0.0142  # m/h
        SM = 0.036  # m

        P_n_1 = P_n = 0.0
        R_n_1 = R_n = 0.0
        F_n_1 = F_n = 0.0

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

            print P_n, I, F_n, I

        return 1


if __name__ == "__main__":
    sr = [[0., 0.], [7.167, 0.0206], [7.333, 0.0212], [7.417, 0.0244], [
        7.583, 0.0270], [7.667, 0.0308], [7.917, 0.0313], [8.000, 0.0346]]
    #sr = [[0.,0.],[0.083,0.0013],[0.667,0.0013],[0.917,0.0216],[1.167,0.0221]]
    t = GreenAmptInfiltrationUnsteadyRain([[0, 2.777e-1, 2, 0]])
