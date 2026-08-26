# @package smoderp2d.courant defines Class Courant which handles the time
# step adjustment


import numpy as np

from smoderp2d.core.general import Globals as Gl, GridGlobals

# Contains variables and methods needed for time step size handling
#
#


class Courant:
    """TODO."""

    # constructor
    #

    def __init__(self):
        """TODO."""
        self.cour_speed = 0
        # critical courant value
        self.cour_crit = 0.95
        self.cour_most = self.cour_crit + 1
        self.cour_most_rill = self.cour_crit + 1.0
        self.cour_coef = 0.5601
        self.cour_least = self.cour_crit * 0.85
        self.i = -1
        self.j = -1
        self.co = 'sheet'
        self.max_delta_t = Gl.maxdt
        self.max_delta_t_mult = 1.0

    #
    def reset(self):
        """Reset the cour_most and cour_speed.

        Happens after each time ste p computation is successfully completed.
        """
        self.cour_most = 0
        self.cour_speed = 0
        self.cour_most_rill = 0

    # Guesses the initial time step.
    #
    #  the guess is based on the maximum \e a and \e b parameters of
    #  the kinematic wave equation and critical water level
    # in case of sheet flow only calculation the water level guess is 0.001 \e
    # m by default
    @staticmethod
    def initial_time_step():
        """TODO."""
        # sumA = sumB = sumHCrit = 0
        # count = 0
        # only_surface = comp_type('surface')

        # for i in sur.rr:
        # for j in sur.rc[i]:
        #     sumA += sur.arr[i, j].a
        #     sumB += sur.arr[i, j].b
        #     sumHCrit += sur.arr[i, j].h_crit
        #     count += 1

        # meanA = sumA/float(count)
        # meanB = sumB/float(count)
        # if (only_surface) :
        # meanHCrit = 0.001
        # else:
        # meanHCrit = sumHCrit/float(count)

        # velGuess = meanA*meanHCrit*meanB*meanB
        # self.initGuess =
        # (math.sqrt(sur.pixel_area)*self.cour_least*self.cour_coef)/velGuess

        # return self.initGuess
        return Gl.maxdt

    #
    def CFL(self, v, delta_t, effect_cont, co):
        """Check the maximum velocity and maximum Courant coefficient.

        Store it in each computational cell.

        :param v: TODO
        :param delta_t: current time step length
        :param effect_cont: TODO
        :param co: TODO
        """
        # step 3-pre: this function used to take a rill_courant grid and
        # fold it in with np.maximum(cour, rill_courant). That term could
        # never win, so it was dropped together with the whole chain that
        # produced it (surface.__runoff -> TimeStep.do_flow -> here).
        #
        # The caller passes v = maximum(v_sheet, v_rill) and, as
        # effect_cont, the very same array that surface.rill_runoff() uses
        # as effect_vrst (Globals.get_mat_effect_cont()). rill_courant is
        # v_rill * delta_t / effect_vrst. With effect_cont > 0, delta_t > 0,
        # v >= v_rill elementwise and 1 / cour_coef = 1.785 > 1:
        #
        #     cour = v / cour_coef * dt / effect_cont
        #          >= 1.785 * v_rill * dt / effect_cont
        #          =  1.785 * rill_courant
        #
        # so cour dominates rill_courant cell by cell. Measured as well,
        # not just derived: zero violations and zero non-finite margins
        # over 148.9e6 valid-cell comparisons in 2441 CFL calls across
        # 1010, 1010-mfda, 4Gor, 4Gti and 5Gor. The maximum rill_courant
        # observed was 1.97, i.e. the term is large in absolute terms -
        # it is dominated, not small.
        #
        # INVARIANT: effect_cont here and effect_vrst in
        # surface.rill_runoff() must stay the same array, and cour_coef
        # must stay below 1. Both are load bearing for the argument above.
        #
        # step 2f: v may still be numpy.ma at the call boundary (masked
        # with GridGlobals.masks) - read raw .data via np.asarray().
        # Unlike the elementwise ma.where() conversions elsewhere in
        # step 2, this function does a *reduction* (argmax) over the
        # whole grid, so the underlying buffer at invalid/out-of-domain
        # cells (whatever arithmetic happened to land there, not
        # necessarily harmless - e.g. division by a near-zero
        # effect_cont) could spuriously win the maximum once the mask no
        # longer excludes it. The search below is therefore explicitly
        # restricted to GridGlobals.valid_idx (step 2a), the same set of
        # cells ma.argmax()/ma.any() would have considered via the mask.
        v = np.asarray(v)
        effect_cont = np.asarray(effect_cont)

        with np.errstate(divide='ignore', invalid='ignore'):
            cour = v / self.cour_coef * delta_t / effect_cont

        valid_idx = GridGlobals.valid_idx
        cour_valid = cour.ravel()[valid_idx]
        if cour_valid.size and np.any(cour_valid > self.cour_most):
            local_argmax = np.argmax(cour_valid)
            flat_idx = valid_idx[local_argmax]
            self.i, self.j = np.unravel_index(flat_idx, cour.shape)
            self.co = co
            self.cour_most = cour[self.i, self.j]
            self.cour_speed = v[self.i, self.j]
        # if rill_courant > self.cour_most_rill:
            # self.cour_most_rill = rill_courant

    # Returns the adjusted/unchanged time step after a time step computation
    # is completed.
    def courant(self, delta_t):
        """Adjust the time step based on Courant.

        :param delta_t: current time step length
        :return: TODO
        """
        # max_delta_t_mult se muze zvetsit
        # pokud je courant v ryhach <= 0.2
        #
        # pokud je courant > 0.5 deje se opak
        # to je ale reseno lokalne
        # v  ./src/processes/rill.py
        #
        # if (self.cour_most_rill < 0.1) :
        # ratio = max(1,ratio-1) # ratio nemuze byt mensi nez 1
        # if ratio == 1 :
        #   self.max_delta_t_mult = 1.0
        # else :
        #     self.max_delta_t_mult = min(1.0, self.max_delta_t_mult*1/(0.9)) #
        #     max_delta_t_mult nemuze byt vetsi nez 1.0

        # ratio se drzi na 10
        # vyse nelze jit
        # proto se zmensuje max_delta_t_mult
        # ktery nasobi vysledne delta
        #
        # if ((ratio > self.maxratio) or (self.cour_most_rill > 1.0)) :
        # ratio = self.maxratio
        # ratio = 1
        # self.max_delta_t_mult *= 0.9

        # pokud je maximalni courant mimo dovolena kryteria
        # mensi nez cour_least a vetsi nez cour_crit
        # explicitne se dopocita dt na nejvetsi mozne
        #                                      xor
        if (self.cour_most < self.cour_least) ^ (self.cour_crit <= self.cour_most):
            # pokud se na povrchu nic nedeje
            # nema se zmena dt cim ridit
            # a zmeni se podle maxima nasobeneho max_delta_t_mult
            # max_delta_t_mult se meni podle ryh, vyse v teto funkci
            if self.cour_speed == 0.0:
                return self.max_delta_t * self.max_delta_t_mult

            effect_cont = Gl.mat_effect_cont[self.i, self.j]
            dt = round(
                effect_cont * self.cour_crit * self.cour_coef / self.cour_speed,
                8
            )

            # nove dt nesmi byt vetsi nez je maxdt * max_delta_t_mult
            # max_delta_t_mult se meni podle ryh, vyse v teto funkci

            # return dt*self.max_delta_t_mult, ratio
            # return min(dt,self.max_delta_t*self.max_delta_t_mult), ratio
            dt_min = min(dt, self.max_delta_t) * self.max_delta_t_mult
            return dt_min

            # pokud je courant v povolenem rozmezi
            # skontrolje se pouze pokud neni vetsi nez maxdt * max_delta_t_mult
            # max_delta_t_mult se meni podle ryh, vyse v teto funkci
        else:
            # return delta_t
            if self.cour_most_rill < 0.5:
                return delta_t
            else:
                return delta_t * self.max_delta_t_mult
