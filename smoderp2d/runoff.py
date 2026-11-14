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
from smoderp2d.core.surface import get_surface, update_state
from smoderp2d.core.subsurface import get_subsurface, get_subsurface_pass
from smoderp2d.core.cumulative_max import Cumulative

from smoderp2d.time_step import TimeStep
from smoderp2d.courant import Courant

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
        self.total_time = 0

        # keep order of a current rainfall interval
        self.tz = 0

        # stores cumulative interception
        self.sum_interception = ma.masked_array(
            np.zeros((r, c), float), mask=GridGlobals.masks
        )

        # maximum amount of iterations
        self.max_iter = 40

        # current number of within time step iterations
        self.iter_ = 0

        # defined by save_vars()
        self.tz_tmp = None
        self.sum_interception_tmp = ma.copy(self.sum_interception)

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

        Should be called at the beginning of each time step.
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

    def update_total_time(self, dt):
        """Rise time after successfully calculated previous time step.

        :param dt: current time step length
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
            self.subsurface = get_subsurface()()
        else:
            self.subsurface = get_subsurface_pass()()

        # maximal and cumulative values of resulting variables
        self.cumulative = Cumulative()

        # in implicit version - courant condition is not used, used for setting time step 
        self.courant = Courant()

        self.delta_t = self.courant.initial_time_step()
        
        self.delta_tmax = self.delta_t

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

        self.record_hydrographs_time_zero()

        Logger.info('-' * 80)

        if Globals.computationType == 'implicit':
            # list of flewdirection vectors - incialization
            self.list_fd = np.zeros((GridGlobals.r, GridGlobals.c, 8), dtype=int)

    def record_hydrographs_time_zero(self):
        """Record values into hydrographs at time zero."""
        zeros = ma.masked_array(
            np.zeros((GridGlobals.r, GridGlobals.c)), mask=GridGlobals.masks
        )

        self.hydrographs.write_hydrographs_record(
            None,
            None,
            self.flow_control,
            self.courant,
            self.delta_t,
            self.surface,
            self.subsurface,
            self.cumulative,
            zeros
        )
        # stream hydrographs at time zero
        self.hydrographs.write_hydrographs_record(
            None,
            None,
            self.flow_control,
            self.courant,
            self.delta_t,
            self.surface,
            self.subsurface,
            self.cumulative,
            zeros,
            True
        )

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
        if Globals.computationType == 'implicit':
            # creates list of flow direction vectors (r*c vectors of length 8 coposed of 1 and 0) 
            for i in range(GridGlobals.r):
                for j in range(GridGlobals.c):
                    self.list_fd[i][j] = D8.inflow_dir(Globals.get_mat_fd(), i, j)
            self.flow_control.save_vars()

        # saves time before the main loop
        Logger.info('Start of computing...')
        Logger.start_time = time.time()
        end_time = Globals.end_time

        # main loop: until the end time
        # var for progress bar
        timeperc_last = 0

        while self.flow_control.compare_time(end_time):

            self.flow_control.save_vars()
            self.flow_control.refresh_iter()
            # Calculate 
            if Globals.computationType == 'explicit':
                # iteration loop
                while self.flow_control.max_iter_reached():

                    self.flow_control.update_iter()
                    self.flow_control.restore_vars()

                    # reset of the courant condition
                    self.courant.reset()

                    # time step size
                    potRain = self.time_step.do_flow(
                        self.surface,
                        self.subsurface,
                        self.delta_t,
                        self.flow_control,
                        self.courant
                    )

                    # stores current time step
                    delta_t_tmp = self.delta_t

                    # update time step size if necessary (based on the courant
                    # condition)
                    self.delta_t = self.courant.courant(self.delta_t)

                    # if current time plus timestep is in next minute
                    # of computation the dt is reduced so the next
                    # computed time is exactly at the top of each minute
                    oldtime = self.flow_control.total_time
                    newtime_minute_floor = (self.flow_control.total_time + self.delta_t) // 60
                    if newtime_minute_floor > oldtime // 60:
                        self.delta_t = newtime_minute_floor * 60. - oldtime

                    # courant conditions is satisfied (time step did
                    # change) the iteration loop breaks
                    if delta_t_tmp == self.delta_t:
                        break

                # Calculate actual rainfall and adds up interception todo:
                # AP - actual is not storred in hydrographs
                actRain = self.time_step.do_next_h(
                    self.surface,
                    self.subsurface,
                    self.rain_arr,
                    self.cumulative,
                    self.hydrographs,
                    self.flow_control,
                    self.courant,
                    potRain,
                    self.delta_t
                )

                # if the iteration exceed the maximal amount of iteration
                # last results are stored in hydrographs
                # and error is raised
                if not self.flow_control.max_iter_reached():
                    self.hydrographs.write_hydrographs_record(
                        None,
                        None,
                        self.flow_control,
                        self.courant,
                        self.delta_t,
                        self.surface,
                        self.subsurface,
                        self.cumulative,
                        actRain
                    )
                    # TODO
                    # post_proc.do(
                    # self.cumulative, Globals.mat_slope, Gl, surface.arr)
                    raise MaxIterationExceeded(
                        self.flow_control.max_iter,
                        self.flow_control.total_time
                    )

                # adjusts the last time step size
                if end_time - self.flow_control.total_time < self.delta_t and \
                        end_time - self.flow_control.total_time > 0:
                    self.delta_t = end_time - self.flow_control.total_time

                # if end time reached the main loop breaks
                if self.flow_control.total_time == end_time:
                    break
            else:
                # implicit version
                actRain, self.delta_t = self.time_step.do_next_h_implicit(
                    self.surface,
                    self.subsurface,
                    self.rain_arr,
                    self.cumulative,
                    self.hydrographs,
                    self.flow_control,
                    self.delta_t,
                    self.delta_tmax,
                    self.list_fd,
                    self.courant    
                )

            if Globals.isStream:
                # calculate outflow from each reach of the stream network
                self.surface.stream_reach_outflow(self.delta_t)
                # calculate inflow to reaches
                self.surface.stream_reach_inflow()
                # record cumulative and maximal results of a reach
                self.surface.stream_cumulative(
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
                    self.subsurface,
                    self.cumulative,
                    actRain,
                    True
                )

            
            # set current times to previous time step
            self.subsurface.curr_to_pre()

            # print raster results in given time steps
            self.times_prt.prt(
                self.flow_control.total_time, self.delta_t, self.surface
            )

            # set current time results to previous time step - for explicit version (implicit version is done in do_next_h_implicit)
            # check if rill flow occur
            if Globals.computationType == 'explicit':
                # update states
                self.surface.arr.state, self.surface.arr.h_last_state1 = update_state(
                    self.surface.arr.h_total_new,
                    self.surface.arr.h_crit,
                    self.surface.arr.h_total_pre,
                    self.surface.arr.state,
                    self.surface.arr.h_last_state1
                )

            self.surface.arr.h_total_pre = ma.copy(self.surface.arr.h_total_new)

            timeperc = 100 * (self.flow_control.total_time + self.delta_t) / end_time
            if timeperc > 99.9 or timeperc - timeperc_last > 5:
                # print progress with 5% step
                Logger.progress(
                    timeperc,
                    self.delta_t,
                    self.flow_control.iter_,
                    self.flow_control.total_time + self.delta_t
                )
                timeperc_last = timeperc

            # proceed to next time
            self.flow_control.update_total_time(self.delta_t)

    def save_output(self):
        """TODO."""
        Logger.info('Saving output data...')
        # perform postprocessing - store results
        self.provider.postprocessing(self.cumulative, self.surface.arr,
                                     self.surface.reach, self.surface.inflows)
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
