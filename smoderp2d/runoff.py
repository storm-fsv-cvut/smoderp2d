""" A computation part of the model SMODERP2D is performer in runoff.py

All date which used by this module was prepared by the provider
before this module is loaded. The data are stored in classes Globals
GridGlobals.

Classes:
    FlowControl - class controls the computation flow, e.g. controls the
    iterations
    Runoff - class contains methods which perform the computation

"""

import time
import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.core.vegetation import Vegetation
from smoderp2d.core.surface import get_surface
from smoderp2d.core.subsurface import Subsurface
from smoderp2d.core.cumulative_max import Cumulative

# from smoderp2d.time_step import TimeStep
from smoderp2d.courant import Courant
from smoderp2d.time_step import TimeStep

from smoderp2d.tools.times_prt import TimesPrt
from smoderp2d.io_functions import hydrographs as wf

from smoderp2d.providers import Logger

from smoderp2d.exceptions import MaxIterationExceeded

import smoderp2d.processes.rainfall as rain_f
import smoderp2d.flow_algorithm.D8 as D8

class FlowControl(object):
    """ Manage variables related to main computational loop."""

    def __init__(self):
        """ Set iteration criteria variables."""
        # number of rows and columns in numpy array
        r, c = GridGlobals.get_dim()

        # type of infiltration
        #  - 0 for philip infiltration is the only
        #    one in current version
        # TODO: seems to be not used (?)
        self.infiltration_type = 0

        # actual time in calculation
        self.total_time = ma.masked_array(
            np.zeros((r, c), float), mask=GridGlobals.masks
        )

        # keep order of a current rainfall interval
        self.tz = 0

        # stores cumulative interception
        self.sum_interception = ma.masked_array(
            np.zeros((r, c), float), mask=GridGlobals.masks
        )

        # factor deviding the time step for rill calculation
        # currently inactive
        self.ratio = ma.masked_array(
            np.ones((r, c), float), mask=GridGlobals.masks
        )

        # maximum amount of iterations
        self.max_iter = 40

        # current number of within time step iterations
        self.iter_ = 0

        # defined by save_vars()
        self.tz_tmp = None
        self.sum_interception_tmp = ma.copy(self.sum_interception)

        # defined by save_ratio()
        self.ratio_tmp = None

    def save_vars(self):
        """Store tz and sum of interception.

        For the case of repeating the time step iteration.
        """
        self.tz_tmp = self.tz
        self.sum_interception_tmp = ma.copy(self.sum_interception)

    def restore_vars(self):
        """Restore tz and sum of interception.

        In case of repeating time step iteration.
        """
        self.tz = self.tz_tmp
        self.sum_interception = ma.copy(self.sum_interception_tmp)

    def refresh_iter(self):
        """Set current number of iteration to zero.

        Should be called at the begining of each time step.
        """
        self.iter_ = 0

    def update_iter(self):
        """Rise iteration count by one.

        In case of iteration within a timestep calculation.
        """
        self.iter_ += 1

    def max_iter_reached(self):
        """Check if iteration exceed a maximum allowed amount."""
        return self.iter_ < self.max_iter

    def save_ratio(self):
        """Save ratio in case of iteration within time step."""
        self.ratio_tmp = self.ratio

    def compare_ratio(self):
        """Check for changing ratio after rill courant criterion check."""
        return self.ratio_tmp == self.ratio

    def update_total_time(self, dt):
        """Rise time after successfully calculated previous time step.

        :param dt: TODO
        """
        self.total_time += dt

    def compare_time(self, end_time):
        """Check if end time is reached.

        :param end_time: TODO
        :return: TODO
        """
        return self.total_time < end_time


class Runoff(object):
    """Performs the calculation.

    run() - this function performs the water level computation
    """

    def __init__(self, provider):
        """Initialize main classes.

        Method defines instances of classes for rainfall, surface,
        stream and subsurface processes handling.

        :param provider: TODO
        """
        self.provider = provider

        # handling print of the solution in given times
        self.times_prt = TimesPrt()

        # flow control
        self.flow_control = FlowControl()

        # handling the actual rainfall amount
        self.rain_arr = Vegetation()

        # handling the surface processes
        self.surface = get_surface()()

        # class handling the subsurface processes if desir
        # TODO: include in data preprocessing
        if Globals.subflow:
            self.subsurface = Subsurface(
                L_sub=0.1,
                Ks=0.005,
                vg_n=1.5,
                vg_l=0.5
            )
        else:
            self.subsurface = Subsurface()

        # maximal and cumulative values of resulting variables
        self.cumulative = Cumulative()

        
        # in implicit version - courant condition is not used, used for setting time step 
        self.courant = Courant()
        self.delta_tmax = self.courant.initial_time_step()
        
        self.delta_t = self.delta_tmax

        Logger.info('Corrected time step is {} [s]'.format(self.delta_t))

        # opens files for storing hydrographs 
        if Globals.get_array_points() is not None:
            self.hydrographs = wf.Hydrographs()
            # TODO
            # arcgis = Globals.arcgis
            # if not arcgis:
            #     with open(os.path.join(Globals.outdir, 'points.txt'), 'w') as fd:
            #         for i in range(len(Globals.array_points)):
            #             fd.write('{} {} {} {}'.format(
            #                 Globals.array_points[i][0], Globals.array_points[i][3],
            #                 Globals.array_points[i][4], os.linesep
            #             ))
        else:
            self.hydrographs = wf.HydrographsPass()

        # method for single time step calculation
        self.time_step = TimeStep()
        # record values into hydrographs at time zero
        self.hydrographs.write_hydrographs_record(
            None,
            None,
            self.flow_control,
            self.courant,
            self.delta_t,
            self.surface,
            self.cumulative,
            ma.masked_array(
                np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
            )
        )
        

        Logger.info('-' * 80)

        # list of flewdirection vectors - incialization
        self.r,self.c = GridGlobals.get_dim()
        self.list_fd = [[] for i in range(self.r*self.c)]

    def run(self):
        """Perform the computation of the water level development.

        The *main loop* which goes through time steps
        has *nested loop* for iterations (in case the
        computation does not converge).

        The computation has been divided in two parts
        First, in iteration (*nested*) loop is calculated
        the surface runoff (to which is the time step
        sensitive) in a function time_step.do_flow()

        Next water balance is performed at each cell of the
        raster. Water level in next time step is calculated by
        a function time_step.do_next_h().

        Selected values are stored in at the end of each loop.
        """
        # creates list of flow direction vectors (r*c vectors of length 8 coposed of 1 and 0) 
        
        for i in range(self.r):
            for j in range(self.c):
                vec_pos = i * self.c + j
                self.list_fd[vec_pos] = D8.inflow_dir(Globals.get_mat_fd(),i,j)

        # saves time before the main loop
        Logger.info('Start of computing...')
        Logger.start_time = time.time()
        end_time = Globals.end_time

        self.flow_control.save_vars()
        # main loop: until the end time

        while ma.any(self.flow_control.compare_time(end_time)):

            self.flow_control.save_vars()
            # Calculate 
           
            actRain, self.delta_t = self.time_step.do_next_h(
                self.surface,
                self.subsurface,
                self.rain_arr,
                self.cumulative,
                self.hydrographs,
                self.flow_control,
                self.delta_t,
                self.delta_tmax,
                self.list_fd    
            )
            
            
            # print raster results in given time steps
            self.times_prt.prt(
                self.flow_control.total_time, self.delta_t, self.surface
            )

            timeperc = 100 * (self.flow_control.total_time + self.delta_t) / end_time
            Logger.progress(
                timeperc.max(),
                self.delta_t.max(),
                self.flow_control.iter_,
                self.flow_control.total_time + self.delta_t
            )
            
            # write hydrographs of reaches
            self.hydrographs.write_hydrographs_record(
                None,
                None,
                self.flow_control,
                self.courant,
                self.delta_t,
                self.surface,
                self.cumulative,
                actRain,
            )

            # proceed to next time
            self.flow_control.update_total_time(self.delta_t)
            
            h_new = self.surface.arr.h_total_new
            h_old = self.surface.arr.h_total_pre
            # if ma.all(abs(h_new - h_old) < 1e-5):
            #     if ma.all(self.delta_t*2 < self.delta_tmax):
            #         self.delta_t = self.delta_t*2
            #     else:
            #         self.delta_t = self.delta_tmax
            self.surface.arr.h_total_pre = ma.copy(self.surface.arr.h_total_new)
                

    def save_output(self):
        """TODO."""
        Logger.info('Saving output data...')
        # perform postprocessing - store results
        self.provider.postprocessing(self.cumulative, self.surface.arr,
                                     self.surface.reach)
        # Logger.progress(100)

        # TODO
        # post_proc.stream_table(Globals.outdir + os.sep, self.surface,
        #                        Globals.streams_loc)

    def __del__(self):
        """TODO."""
        Logger.info('-' * 80)
        Logger.info('Total computing time: {} sec'.format(
            int(time.time() - Logger.start_time))
        )
