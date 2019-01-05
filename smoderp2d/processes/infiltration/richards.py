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
        self.ks = ks
        self.dx = dx

        # t-1 solution with dirichlet boundary condition
        self.dir_pre = np.zeros([n], float)
        self.dir_pre.fill(-0)
        # t   solution with dirichlet boundary condition
        self.dir_new = np.zeros([n], float)
        self.dir_new.fill(-1)
        # for i, item in enumerate(self.dir_new):
        #print -i, item

        # t-1 solution with neumann boundary condition
        self.neu_pre = np.zeros([n], float)
        # t   solution with neumann boundary condition
        self.neu_new = np.zeros([n], float)
        self.neu_new.fill(-0.1)


class RichardsInfiltration(BaseInfiltration):

    def __init__(self, combinatIndex):

        self._combinat_index = combinatIndex

        self._n = 101
        self._dx = 0.01

        self._n_soils = len(combinatIndex)

        # A matrix of Ah = b linear system
        # TODO make it sparse
        self._A = np.zeros([self._n, self._n], float)
        # b size of Ah = b linear system
        self._b = np.zeros([self._n], float)

        # setup solver
        self._solver = np.linalg.solve

        # this list of soil profile instances
        # should in terms of indices correspond
        # to id in combinatIndex array
        self._soil = []

        for i in range(self._n_soils):
            self._soil.append(SoilProfile(n=self._n, dx=self._dx, tr=0.2,
                                          ts=0.5, vg_a=0.99, vg_n=3.5, ks=self._combinat_index[i][1]))

    def _fill_Ab(self, sp, dt):
        #  Fills the linear system for dirichlet boundary condition.

        for i in range(self._n):
            if (i == 0):
                self._b[i] = -0.00
                self._A[i][i] = 1.
            elif (i == (self._n-1)):
                self._b[i] = -1.0
                self._A[i][i] = 1.
            else:
                C_pre = self._dvg_theta_dh(sp, sp.dir_pre[i])
                h_ipre = sp.dir_pre[i]
                K1 = self._mualem_K(sp, (sp.dir_new[i+1] + sp.dir_new[i])/2)
                K2 = self._mualem_K(sp, (sp.dir_new[i] + sp.dir_new[i-1])/2)

                self._b[i] = - C_pre/dt*h_ipre - (+ K1/sp.dx - K2/sp.dx)

                self._A[i][i-1] = K1/sp.dx**2.

                C_new = self._dvg_theta_dh(sp, sp.dir_new[i])
                self._A[i][i] = - (C_new/dt + K1/sp.dx**2. + K2/sp.dx**2.)

                self._A[i][i+1] = K2/sp.dx**2.

    def _solve_step(self, sp, dt):
        """ Solve one step in richards equation for i ingle soil profile.

        :param sp: instance of SoilProfile class -> single soil profile
        :param dt: time step
        """

        iter_ = 1
        err = 3e99
        while self._no_converged(err):
            if self._iter_check(iter_):
                break
            self._fill_Ab(sp, dt)
            sp.dir_new_p = sp.dir_new.copy()
            sp.dir_new = self._solver(self._A, self._b)
            err = sum((sp.dir_new_p - sp.dir_new)**2.)
            iter_ += 1
        sp.dir_pre = sp.dir_new.copy()
        for i, item in enumerate(sp.dir_new):
            print i, item

    def _no_converged(self, err):
        """ Convergence criterion"""

        # minimal allowd error
        err_min = 1e-3
        if (err < err_min):
            return False
        else:
            return True

    def _iter_check(self, iter_):
        """ Checks the iteration count """

        max_iter = 40
        if (iter_ > max_iter):
            # TODO raise error
            return True
        else:
            return False

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
            kr = (1. - (-(a*h))**(m*n)/(1. + (-(a*h))**n)
                  ** m)**2./(1. + (-(a*h))**n)**(m/2.)

        return kr*sp.ks

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
            C = a*m*n*(-tr + ts)*(-(a*h))**(-1 + n)*(1 + (-(a*h))**n)**(-1 - m)

        return C

    def precalc(self, dt, total_time):
        """ Precalculates potential infiltration got a given soil.
        The precalculated value is storred in the self._combinat_index
        """
        for iii in self._combinat_index:
            index = iii[0]
            iii[3] = self._solve_step(self._soil[index], dt)

    def current_infiltration(self, soil, bil):
        raise NotImplemented("Not implemented for Richards infiltration")


if instance:
    t = RichardsInfiltration([[0, 2.777e-1, 2, 0]])
    # calc timestep 1 sec
    t.precalc(1, 5.0)
    # calc timestep 5 secs
    t.precalc(5, 5.0)
