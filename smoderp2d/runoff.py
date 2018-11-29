"""The computing area is determined  as well as the boundary cells.

Vypocet probiha v zadanem casovem kroku, pripade je cas kracen podle
"Couranotva kriteria":
 - vystupy jsou rozdelieny do \b zakladnich a \b doplnkovych, podle zvoleneh typu vypoctu
 - zakladni
 - maximalni vyska haladiny plosneho odtoku
"""

import time
import os

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
from smoderp2d.core.surface import sheet_to_rill
from smoderp2d.tools.tools import make_sur_raster
from smoderp2d.providers import Logger

from smoderp2d.exceptions import MaxIterationExceeded


class FlowControl(object):
    """FlowControl manage variables contains variables related to main
    computational loop."""

    def __init__(self):
        # type of infiltration
        #  - 0 for philip infiltration is the only
        #    one in current version
        # TODO: seems to be not used (?)
        self.infiltration_type = 0

        # actual time in calculation
        self.total_time = 0.0

        # keep order of a curent rainfall interval
        self.tz = 0

        # stores cumulative interception
        self.sum_interception = 0

        # factor deviding the time step for rill calculation
        # currently inactive
        self.ratio = 1

        # naximum amount of iterations
        self.max_iter = 40

        # current number of wihtin time step iterations
        self.iter_ = 0

    def save_vars(self):
        """Store tz and sum of interception
        in case of repeating time time stem iteration.
        """
        self.tz_tmp = self.tz
        self.sum_interception_tmp = self.sum_interception

    def restore_vars(self):
        """Restore tz and sum of interception
        in case of repeating time time stem iteration.
        """
        self.tz = self.tz_tmp
        self.sum_interception = self.sum_interception_tmp

    def refresh_iter(self):
        """Set current number of iteration to
        zero at the begining of each time step.
        """
        self.iter_ = 0

    def upload_iter(self):
        """Rises iteration count by one
        in case of iteration within a timestep calculation.
        """
        self.iter_ += 1

    def max_iter_reached(self):
        """Check if iteration exceed a maximum allowed amount.
        """
        return self.iter_ < self.max_iter

    def save_ratio(self):
        """Saves ration in case of interation within time step.
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
        self.courant_rill = Courant()

        self.delta_t = self.courant.initial_time_step()
        self.courant.set_time_step(self.delta_t)
        self.courant_rill.set_time_step(self.delta_t)

        Logger.info('Corrected time step is {} [s]'.format(self.delta_t))

        # opens files for storing hydrographs
        if Globals.points and Globals.points != "#":
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
        rr, rc = GridGlobals.get_region_dim()
        for i in rr:
            for j in rc[i]:
                self.hydrographs.write_hydrographs_record(
                    i,
                    j,
                    0,
                    0,
                    0,
                    0.0
                )

        Logger.info('-' * 80)

    def run(self):
        # saves time before the main loop
        start = time.time()
        Logger.info('Start of computing...')

        i = j = 0
        rr, rc = GridGlobals.get_region_dim()
        # main loop: until the end time
        while self.flow_control.compare_time(Globals.end_time):

            self.flow_control.save_vars()
            self.flow_control.refresh_iter()

            # iteration loop for sheet flow
            while self.flow_control.max_iter_reached():

                self.flow_control.upload_iter()
                self.flow_control.restore_vars()

                # reset of the courant condition
                self.courant.reset()
                self.flow_control.save_ratio()

                self.time_step.do_sheet_flow(
                    self.surface,
                    self.subsurface,
                    self.delta_t,
                    self.flow_control,
                    self.courant,
                    self.courant_rill
                )

                # stores current time step
                delta_t_tmp = self.delta_t

                # update time step size if necessary (based on the courant
                # condition)
                self.delta_t = self.courant.courant(self.delta_t)

                # courant conditions is satisfied (time step did
                # change) the iteration loop breaks
                if delta_t_tmp == self.delta_t and self.flow_control.compare_ratio():
                    break

            if not self.flow_control.max_iter_reached():
                raise MaxIterationExceeded(max_iter, total_time)

            # calculate sheet to rill
            sheet_to_rill(self.surface)

            N = 3
            # calculates the rill h
            for k in range(N):
                self.time_step.do_rill_flow(
                    self.surface,
                    self.delta_t,
                    self.flow_control,
                    self.courant_rill,
                    N
                )
                for i in rr:
                    for j in rc[i]:
                        self.surface.arr[i][j].h_rill_pre = self.surface.arr[i][j].h_rill_new

            # adjusts the last time step size
            if (Globals.end_time - self.flow_control.total_time) < self.delta_t and \
               (Globals.end_time - self.flow_control.total_time) > 0:
                self.delta_t = Globals.end_time - self.flow_control.total_time

            # proceed to next time
            self.flow_control.update_total_time(self.delta_t)

            # if end time reached the main loop breaks
            if self.flow_control.total_time == Globals.end_time:
                break

            timeperc = 100 * (self.flow_control.total_time +
                              self.delta_t) / Globals.end_time
            Logger.progress(
                timeperc,
                self.delta_t,
                self.flow_control.iter_,
                self.flow_control.total_time + self.delta_t
            )

            make_sur_raster(self.surface.arr, Globals,
                            self.flow_control.total_time, Globals.outdir)

            #print self.surface.arr[i][j].h_sheet_new, self.surface.arr[i][j].h_rill_new,self.surface.arr[i][j].h_sheet_new+self.surface.arr[i][j].h_rill_new
            # raw_input()
            for i in rr:
                for j in rc[i]:
                    self.hydrographs.write_hydrographs_record(
                        i,
                        j,
                        self.flow_control.total_time + self.delta_t,
                        self.surface.arr[i][j].h_sheet_new,
                        self.surface.arr[i][j].h_rill_new,
                        self.surface.arr[i][j].rill_width
                    )

            # calculate outflow from each reach of the stream network
            self.surface.stream_reach_outflow(self.delta_t)
            # calculate inflow to reaches
            self.surface.stream_reach_inflow()
            # record cumulative and maximal results of a reach
            self.surface.stream_cumulative(
                self.flow_control.total_time + self.delta_t)

            # set current times to previous time step
            self.subsurface.curr_to_pre()

            # write hydrographs of reaches
            # self.hydrographs.write_hydrographs_record(
            # i,
            # j,
            # self.flow_control,
            # self.courant,
            # self.delta_t,
            # self.surface,
            # self.subsurface,
            # actRain,
            # True
            # )

            # print raster results in given time steps
            self.times_prt.prt(self.flow_control.total_time,
                               self.delta_t, self.surface)

            # set current time results to previous time step
            # check if rill flow occur
            for i in self.surface.rr:
                for j in self.surface.rc[i]:

                    self.surface.arr[i][j].h_sheet_pre = self.surface.arr[i][j].h_sheet_new
                    # if self.surface.arr[i][j].state == 0:
                    # if self.surface.arr[i][j].h_total_new > self.surface.arr[i][j].h_crit:
                    #self.surface.arr[i][j].state = 1

                    # if self.surface.arr[i][j].state == 1:
                    # if self.surface.arr[i][j].h_total_new < self.surface.arr[i][j].h_total_pre:
                    #self.surface.arr[i][j].h_last_state1 = self.surface.arr[i][j].h_total_pre
                    #self.surface.arr[i][j].state = 2

                    # if self.surface.arr[i][j].state == 2:
                    # if self.surface.arr[i][j].h_total_new > self.surface.arr[i][j].h_last_state1:
                    #self.surface.arr[i][j].state = 1

        Logger.debug('Max courant in sheet flow {}'.format(
            self.courant.tot_cour_most))
        Logger.debug('Max courant in rill  flow {}'.format(
            self.courant_rill.tot_cour_most))

        Logger.info('Saving data...')

        Logger.info('')
        Logger.info('-' * 80)
        Logger.info('Total computing time: {}'.format(time.time() - start))

        # TODO
        # post_proc.do(self.cumulative, Globals.mat_slope, Gl, self.surface.arr)

        post_proc.stream_table(Globals.outdir + os.sep,
                               self.surface, Globals.toky_loc)

        # TODO: print stats in better way
        # import platform
        # if platform.system() == "Linux":
        #     pid = os.getpid()
        #     Logger.info("/proc/{}/status reading".format(pid))
        #     with open(os.path.join('/', 'proc', str(pid), "status"), 'r') as fp:
        #         for i, line in enumerate(fp):
        #             if i >= 11 and i <= 23:
        #                 Logger.info(line.rstrip(os.linesep))
