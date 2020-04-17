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
import os
import numpy as np

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.core.vegetation import Vegetation
from smoderp2d.core.surface import Surface
from smoderp2d.core.subsurface import Subsurface
from smoderp2d.core.cumulative_max import Cumulative

from smoderp2d.time_step import TimeStep
from smoderp2d.courant import Courant

from smoderp2d.tools.times_prt import TimesPrt
from smoderp2d.io_functions import post_proc
from smoderp2d.io_functions import hydrographs as wf

from smoderp2d.providers import Logger

from smoderp2d.exceptions import MaxIterationExceeded

class FlowControl(object):
    """ Manage variables related to main computational loop. """

    def __init__(self):
        """ Set iteration criteria variables. """

        # number of rows and columns in numpy array
        r, c = GridGlobals.get_dim()

        # type of infiltration
        #  - 0 for philip infiltration is the only
        #    one in current version
        # TODO: seems to be not used (?)
        self.infiltration_type = 0

        # actual time in calculation
        self.total_time = 0.0

        # keep order of a current rainfall interval
        self.tz = 0

        # stores cumulative interception
        self.sum_interception = np.zeros((r, c), float)

        # factor deviding the time step for rill calculation
        # currently inactive
        self.ratio = 1

        # maximum amount of iterations
        self.max_iter = 40

        # current number of within time step iterations
        self.iter_ = 0

        # defined by save_vars()
        self.tz_tmp = None
        self.sum_interception_tmp = np.copy(self.sum_interception)

        # defined by save_ratio()
        self.ratio_tmp = None
        
    def save_vars(self):
        """Store tz and sum of interception
        in case of repeating time time stem iteration.
        """
        self.tz_tmp = self.tz
        self.sum_interception_tmp = np.copy(self.sum_interception)

    def restore_vars(self):
        """Restore tz and sum of interception
        in case of repeating time time stem iteration.
        """
        self.tz = self.tz_tmp
        self.sum_interception = np.copy(self.sum_interception_tmp)

    def refresh_iter(self):
        """Set current number of iteration to
        zero at the begining of each time step.
        """
        self.iter_ = 0

    def update_iter(self):
        """Rises iteration count by one
        in case of iteration within a timestep calculation.
        """
        self.iter_ += 1

    def max_iter_reached(self):
        """Check if iteration exceed a maximum allowed amount.
        """
        return self.iter_ < self.max_iter

    def save_ratio(self):
        """Saves ratio in case of iteration within time step.
        """
        self.ratio_tmp = self.ratio

    def compare_ratio(self):
        """Check for changing ratio after rill courant criterion check.
        """
        return self.ratio_tmp == self.ratio

    def update_total_time(self, dt):
        """Rises time after successfully calculated previous time step.
        """
        self.total_time += dt

    def compare_time(self, end_time):
        """Checkes if end time is reached.
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
        """
        self.provider = provider
        
        # handling print of the solution in given times
        self.times_prt = TimesPrt()

        # flow control
        self.flow_control = FlowControl()

        # handling the actual rainfall amount
        self.rain_arr = Vegetation()

        # handling the surface processes
        self.surface = Surface()

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

        # handle times step changes based on Courant condition
        self.courant = Courant()
        self.delta_t = self.courant.initial_time_step(self.surface)
        self.courant.set_time_step(self.delta_t)
        Logger.info('Corrected time step is {} [s]'.format(self.delta_t))

        # opens files for storing hydrographs
        if Globals.points and Globals.points != "#":
            self.hydrographs = wf.Hydrographs()
            ### TODO
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
        rr, rc = GridGlobals.get_region_dim()
        for i in rr:
            for j in rc[i]:
                self.hydrographs.write_hydrographs_record(
                    i,
                    j,
                    self.flow_control,
                    self.courant,
                    self.delta_t,
                    self.surface,
                    self.subsurface,
                    0.0
                )
        # record values into stream hydrographs at time zero
        self.hydrographs.write_hydrographs_record(
            i,
            j,
            self.flow_control,
            self.courant,
            self.delta_t,
            self.surface,
            self.subsurface,
            0.0,
            True
        )

        Logger.info('-' * 80)

    def run(self):
        """ The computation of the water level development 
        is performed here. 
        
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


        # saves time before the main loop
        Logger.info('Start of computing...')
        Logger.start_time = time.time()

        # main loop: until the end time
        i = j = 0 # TODO: rename vars (variable overlap)
        while self.flow_control.compare_time(Globals.end_time):

            self.flow_control.save_vars()
            self.flow_control.refresh_iter()

            # iteration loop
            while self.flow_control.max_iter_reached():

                self.flow_control.update_iter()
                self.flow_control.restore_vars()

                # reset of the courant condition
                self.courant.reset()
                self.flow_control.save_ratio()

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
                self.delta_t, self.flow_control.ratio = self.courant.courant(
                    potRain, self.delta_t, self.flow_control.ratio
                )

                # courant conditions is satisfied (time step did
                # change) the iteration loop breaks
                if delta_t_tmp == self.delta_t and self.flow_control.compare_ratio():
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
                for i in Globals.rr:
                    for j in Globals.rc[i]:
                        self.hydrographs.write_hydrographs_record(
                            i,
                            j,
                            self.flow_control,
                            self.courant,
                            self.delta_t,
                            self.surface,
                            self.subsurface,
                            self.curr_rain
                        )
                # TODO
                # post_proc.do(self.cumulative, Globals.mat_slope, Gl, surface.arr)
                raise MaxIterationExceeded(max_iter, total_time)

            # adjusts the last time step size
            if (Globals.end_time - self.flow_control.total_time) < self.delta_t and \
               (Globals.end_time - self.flow_control.total_time) > 0:
                self.delta_t = Globals.end_time - self.flow_control.total_time

            # proceed to next time
            self.flow_control.update_total_time(self.delta_t)

            # if end time reached the main loop breaks
            if self.flow_control.total_time == Globals.end_time:
                break

            timeperc = 100 * (self.flow_control.total_time + self.delta_t) / Globals.end_time
            Logger.progress(
                timeperc,
                self.delta_t,
                self.flow_control.iter_,
                self.flow_control.total_time + self.delta_t
            )

            # calculate outflow from each reach of the stream network
            self.surface.stream_reach_outflow(self.delta_t)
            # calculate inflow to reaches
            self.surface.stream_reach_inflow()
            # record cumulative and maximal results of a reach
            self.surface.stream_cumulative(self.flow_control.total_time + self.delta_t)

            # set current times to previous time step
            self.subsurface.curr_to_pre()

            # write hydrographs of reaches
            self.hydrographs.write_hydrographs_record(
                i,
                j,
                self.flow_control,
                self.courant,
                self.delta_t,
                self.surface,
                self.subsurface,
                actRain,
                True
            )

            # print raster results in given time steps
            self.times_prt.prt(self.flow_control.total_time, self.delta_t, self.surface)

            # set current time results to previous time step
            # check if rill flow occur
            for i in self.surface.rr:
                for j in self.surface.rc[i]:
                    if self.surface.arr[i][j].state == 0:
                        if self.surface.arr[i][j].h_total_new > self.surface.arr[i][j].h_crit:
                            self.surface.arr[i][j].state = 1

                    if self.surface.arr[i][j].state == 1:
                        if self.surface.arr[i][j].h_total_new < self.surface.arr[i][j].h_total_pre:
                            self.surface.arr[i][j].h_last_state1 = self.surface.arr[i][j].h_total_pre
                            self.surface.arr[i][j].state = 2

                    if self.surface.arr[i][j].state == 2:
                        if self.surface.arr[i][j].h_total_new > self.surface.arr[i][j].h_last_state1:
                            self.surface.arr[i][j].state = 1

                    self.surface.arr[i][j].h_total_pre = self.surface.arr[i][j].h_total_new


        # perform postprocessing - store results
        Logger.info('Saving output data...')
        self.provider.postprocessing(self.cumulative, self.surface.arr,
                self.surface.reach)

        # TODO
        # post_proc.stream_table(Globals.outdir + os.sep, self.surface,
        #                        Globals.streams_loc)

        Logger.info('-' * 80)
        Logger.info('Total computing time: {}'.format(
            time.time() - Logger.start_time)
        )

        # TODO: print stats in better way
        # import platform
        # if platform.system() == "Linux":
        #     pid = os.getpid()
        #     Logger.info("/proc/{}/status reading".format(pid))
        #     with open(os.path.join('/', 'proc', str(pid), "status"), 'r') as fp:
        #         for i, line in enumerate(fp):
        #             if i >= 11 and i <= 23:
        #                 Logger.info(line.rstrip(os.linesep))
