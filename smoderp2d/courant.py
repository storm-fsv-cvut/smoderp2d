# @package smoderp2d.courant defines Class Courant which handels the time step adjustement


import math
from smoderp2d.providers import Logger

from smoderp2d.core.general import Globals as Gl, GridGlobals

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
        self.cour_least = 0.3
        self.i = -1
        self.j = -1
        self.co = 'sheet'
        self.co_pre = 'sheet'
        self.maxratio = 10
        self.max_delta_t = Gl.maxdt
        self.max_delta_t_mult = 1.2

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

    def initial_time_step(self):
        """ init time step """
        return Gl.maxdt

    # Checks and store in each computational cell the maximum velocity and maximum Courant coefficient
    #
    def CFL(self, i, j, v_sheet_new, delta_t):
        cour = v_sheet_new * delta_t / GridGlobals.get_size()[0]
        # cour = max(cour, rill_courant)

        if cour > self.cour_most:
            self.i = i
            self.j = j
            self.cour_speed = v_sheet_new

    def courant(self, delta_t):
        """ adjust the time step 
        
        :param delta_t: current time step
        """

        if (self.cour_crit <= self.cour_most):
            if (self.cour_speed == 0.0):
                return self.max_delta_t
            dt = delta_t / self.max_delta_t_mult
            Logger.warning('Decrease time step to {0:.4f}'.format(dt))
            return dt

        if (self.cour_most < self.cour_least):
            if (delta_t * self.max_delta_t_mult > self.max_delta_t) :
                dt = self.max_delta_t
            else :
                dt = delta_t * self.max_delta_t_mult 
                Logger.warning('Increase time step to {0:.4f}'.format(dt))
            return dt

        return delta_t
