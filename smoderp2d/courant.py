# @package smoderp2d.courant defines Class Courant which handels the time step adjustement


import math
import tensorflow as tf
from smoderp2d.providers import Logger

from smoderp2d.core.general import Globals as Gl

# Contains variables and methods needed for time step size handling
#
#


class Courant():

    # constructor
    #

    def __init__(self):
        # self.orig_dt = dt
        self.maxh = 0
        self.cour_speed = 0
        # citical courant value
        self.cour_crit = 0.95
        self.cour_most = self.cour_crit + 1.0
        self.cour_most_rill = self.cour_crit + 1.0
        self.cour_coef = 0.5601
        self.cour_least = self.cour_crit * 0.85
        self.i = -1
        self.j = -1
        self.co = 'sheet'
        self.co_pre = 'sheet'
        self.maxratio = 10
        self.max_delta_t = Gl.maxdt
        self.max_delta_t_mult = 1.0

    # Store the original guess time step
    #
    def set_time_step(self, dt):
        self.orig_dt = dt

    # Resets the self.cour_most and self.cour_speed after each time stop computation is successfully completed
    #
    def reset(self):
        self.cour_most = 0
        self.cour_speed = 0
        self.cour_most_rill = 0

    # Guesses the initial time step.
    #
    #  the guess is based on the maximum \e a and \e b parameters of the kinematic wave equation and critical water level
    # in case of sheet flow only calculation the water level guess is 0.001 \e
    # m by default
    def initial_time_step(self, sur):
        # sumA = sumB = sumHCrit = 0
        # count = 0
        # only_surface = comp_type('surface')

        # for i in sur.rr:
        # for j in sur.rc[i]:
          # sumA += sur.arr[i][j].a
          # sumB += sur.arr[i][j].b
          # sumHCrit += sur.arr[i][j].h_crit
          # count += 1

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

    # Checks and store in each computational cell the maximum velocity and maximum Courant coefficient
    #
    def CFL(self, h_total_pre, v, delta_t, mat_efect_cont, co, rill_courant):
        cour = v / self.cour_coef * delta_t / mat_efect_cont
        cour = tf.math.maximum(cour, rill_courant)

        max_i = tf.argmax(tf.reduce_max(cour, axis=1))
        max_j = tf.argmax(cour, axis=1)[tf.argmax(tf.reduce_max(cour, axis=1))]
        cond = cour[max_i, max_j] > self.cour_most

        self.i = tf.where(cond, max_i, self.i)
        self.j = tf.where(cond, max_j, self.j)
        self.co = tf.where(cond, co, self.co)
        self.cour_most = tf.where(cond, cour[max_i, max_j], self.cour_most)
        self.maxh = tf.where(cond, h_total_pre[max_i, max_j], self.maxh)
        self.cour_speed = tf.where(cond, v[max_i, max_j], self.cour_speed)

    # Returns the adjusted/unchanged time step after a time step computation is completed.
    #
    #  Also returns the ratio for the rill computation division.
    #
    def courant(self, rainfall, delta_t, ratio):

        # ratio se muze zmensit  a max_delta_t_mult zvetsit
        # pokud je courant v ryhach <= 0.2
        #
        # pokud je courant > 0.5 deje se opak
        # to je ale reseno lokalne
        # v  ./src/processes/rill.py
        #
        # if (self.cour_most_rill < 0.1) :
        # ratio = max(1,ratio-1) # ratio nemuze byt mensi nez 1
        # if ratio == 1 :
            # self.max_delta_t_mult = 1.0
        # else :
            # self.max_delta_t_mult = min(1.0, self.max_delta_t_mult*1/(0.9)) #
            # max_delta_t_mult nemuze byt vetsi nez 1.0

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
        # if ((self.cour_most < self.cour_least) != (self.cour_crit <= self.cour_most)):

        if not tf.equal(self.cour_most < self.cour_least,
                        self.cour_crit <= self.cour_most):

        # pokud se na povrchu nic nedeje
        # nema se zmena dt cim ridit
        # a zmeni se podle maxima nasobeneho max_delta_t_mult
        # max_delta_t_mult se meni podle ryh, vyse v teto funkci
        #
            if tf.equal(self.cour_speed, 0.0):
                return self.max_delta_t * self.max_delta_t_mult, ratio

            # dt = tf.round(
            #     (Gl.mat_efect_cont[self.i, self.j] * self.cour_crit * self.cour_coef) /
            #      self.cour_speed,
            #     4)

            dt = (Gl.mat_efect_cont[self.i, self.j] * self.cour_crit *
                  self.cour_coef) / self.cour_speed

            # nove dt nesmi byt vetsi nez je maxdt * max_delta_t_mult
            # max_delta_t_mult se meni podle ryh, vyse v teto funkci

            # return dt*self.max_delta_t_mult, ratio
            # return min(dt,self.max_delta_t*self.max_delta_t_mult), ratio
            # print 'asdf', self.cour_speed, dt, self.max_delta_t_mult
            return min(dt * self.max_delta_t_mult, self.max_delta_t * self.max_delta_t_mult), ratio

        # pokud je courant v povolenem rozmezi
        # skontrolje se pouze pokud neni vetsi nez maxdt * max_delta_t_mult
        # max_delta_t_mult se meni podle ryh, vyse v teto funkci
        else:
            # print 'fdafdsfasdfadsfadsfadsfaf'
            # return delta_t, ratio
            # print 'asdf', dt, dt*self.max_delta_t_mult, ratio
            if ((ratio <= self.maxratio) and (self.cour_most_rill < 0.5)):
                return delta_t, ratio
            else:
                return delta_t * self.max_delta_t_mult, ratio

        Logger.critical(
            'courant.cour() missed all its time step conditions\n no rule to preserve or change the time step!'
        )
