# @package smoderp2d.runoff loop of the modul
#
#  The computing area is determined  as well as the boundary cells.
#
#  \e vypocet probiha v zadanem casovem kroku, pripade je cas kracen podle \b "Couranotva kriteria":
#    - vystupy jsou rozdelieny do \b zakladnich a \b doplnkovych, podle zvoleneh typu vypoctu
#    - \b zakladni
#        - @return \b h0 maximalni vyska haladiny plosneho odtoku
#


#!/usr/bin/python
# -*- coding: latin-1 -*-
# Surface and subsurface rutine
# Created by Petr Kavka, FCE, CTU Prague, 2015

__author__ = "edlman"
__date__ = "$29.12.2015 18:31:25$"

# INITIAL SETTINGS:
#
# importing system moduls
# import math
import numpy as np
import time
import os
import sys
# from   smoderp2d.classes_main_arrays import *
# from   smoderp2d.tools.resolve_partial_computing import *

# importing classes


from smoderp2d.main_classes.General import Globals as Gl
from smoderp2d.main_classes.Vegetation import Vegetation
from smoderp2d.main_classes.Surface import Surface

from smoderp2d.main_classes.Subsurface import Subsurface
from smoderp2d.main_classes.CumulativeMax import Cumulative
from smoderp2d.time_step import TimeStep

import smoderp2d.constants as constants
from smoderp2d.courant import Courant
import smoderp2d.tools.tools as tools
import smoderp2d.io_functions.post_proc as post_proc
import smoderp2d.io_functions.prt as prt
import smoderp2d.io_functions.progress_bar as progress_bar
from smoderp2d.tools.tools import comp_type
from smoderp2d.tools.times_prt import TimesPrt
from smoderp2d.tools.tools import get_argv

from smoderp2d.exceptions import MaxIterationExceeded



# FlowControl manage variables contains variables
#
#  class contains variables which controls
#  are related to main computational loop
class FlowControl():

    def __init__(self):

        # type of infiltration
        # 0 for philip infiltration is the only one
        # in current version
        self.infiltrationType = int(0)

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
        self.maxIter = 40

        # current number of wihtin time step iterations
        self.iter_ = 0

    # store tz and sum of interception
    # in case of repeating time time stem iteration
    def save_vars(self):
        self.tz_tmp = self.tz
        self.sum_interception_tmp = self.sum_interception
    # restore tz and sum of interception
    # in case of repeating time time stem iteration

    def restore_vars(self):
        self.tz = self.tz_tmp
        self.sum_interception = self.sum_interception_tmp

    # set current number of iteratio to
    # zero at the begining of each time step
    def refresh_iter(self):
        self.iter_ = 0
    # rises iteration count by one
    # in case of iteration within a timestep calculation

    def upload_iter(self):
        self.iter_ += 1
    # check if iteration exceed a maximum allowed amount

    def max_iter_reached(self):
        return self.iter_ < self.maxIter

    # saves ration in case of interation within time step
    def save_ratio(self):
        self.ratio_tmp = self.ratio
    # check for changing ratio after rill courant criterion check

    def compare_ratio(self):
        return self.ratio_tmp == self.ratio

    # rises time after successfully calculated previous time step
    def update_total_time(self, dt):
        self.total_time += dt

    # checkes it end time is reached
    def compare_time(self, end_time):
        return self.total_time < end_time


# Initialize main classes
#
# method defines instances of classes
# for rainfall, surface, stream and subsurface processes handling
def init_classes():

    # boolean variables defines presence of process
    # isRill, subflow, stream, diffuse, = comp_type()

    # instance of class for handling print of the solution in given times
    times_prt = TimesPrt()

    flowControl = FlowControl()

    # instance of class handling the actual rainfall amount
    rain_arr = Vegetation()

    # instance of class handling the surface processes
    surface = Surface()

    # instance of class handling the subsurface processes if desire
    # doto: include in data preprocessing
    if (Gl.subflow):
        subsurface = Subsurface(
            L_sub=0.1,
            Ks=0.005,
            vg_n=1.5,
            vg_l=0.5)
    else:
        subsurface = Subsurface()

    # instance of class which stores maximal and cumulative values of
    # resulting variables
    cumulative = Cumulative()

    # instance of class which handle times step changes
    # based on Courant condition
    courant = Courant()
    delta_t = courant.initial_time_step(surface)
    courant.set_time_step(delta_t)

    prt.message('Corrected time step is', delta_t, '[s]')

    # instance of class which opens files for storing hydrographs
    import io_functions.hydrographs as wf
    if len(Gl.array_points) > 0:
        hydrographs = wf.Hydrographs()
        arcgis = Gl.arcgis
        if not(arcgis):
            with open(Gl.outdir+'/points.txt', 'w') as f:
                for i in range(len(Gl.array_points)):
                    f.write(str(Gl.array_points[i][0]) + ' ' + str(
                        Gl.array_points[i][3]) + ' ' + str(Gl.array_points[i][4]) + '\n')
            f.closed
    else:
        hydrographs = wf.HydrographsPass()

    # instance of class contains method for single time step calculation
    time_step = TimeStep()

    # self,i,j,fc,courant,dt,surface,subsurface,currRain,inStream=False,sep=';')
    # Record values into hydrographs at time zero
    for i in Gl.rr:
        for j in Gl.rc[i]:
            hydrographs.write_hydrographs_record(
                i,
                j,
                flowControl,
                courant,
                delta_t,
                surface,
                subsurface,
                0.0)

    # Record values into stream hydrographs at time zero
    hydrographs.write_hydrographs_record(
        i,
        j,
        flowControl,
        courant,
        delta_t,
        surface,
        subsurface,
        0.0,
        True)

    return delta_t, flowControl, rain_arr, surface, subsurface, cumulative, courant, hydrographs, time_step, times_prt

    prt.message(
        "--------------------- ------------------- ---------------------")


# Class runoff performs the calculation
#
#
class Runoff():

    # Method run call method for initialization
    #  and contains the main time loop

    def run(self):

        # delta_t, times_prt, infiltrationType, total_time, tz,
        # sum_interception, ratio, maxIter, \
        delta_t, flowControl, rain_arr, surface, subsurface, cumulative, courant, hydrographs, time_step, times_prt = init_classes(
        )

        i = 0
        j = 0
        # saves time before the main loop
        start = time.time()
        prt.message('Start of computing ')

        # main loop
        # until the end time
        while (flowControl.compare_time(Gl.end_time)):

            flowControl.save_vars()
            # tz_tmp               = tz                # stores the order of the rainfall interval in case of the time step size reduction
            # sum_interception_tmp = sum_interception  # stores cumulative
            # interception in case of the time step size reduction

            flowControl.refresh_iter()
            # iter_                = 0

            # iteration loop
            while (flowControl.max_iter_reached()):

                flowControl.upload_iter()
                # iter_ += 1

                flowControl.restore_vars()
                # tz                 = tz_tmp                # load the order of current rainfall interval
                # sum_interception   = sum_interception_tmp  # load the current
                # cumulative interception

                # reset of the courant condition
                courant.reset()
                flowControl.save_ratio()
                # ratio_tmp = ratio

                # time_step.do_flow return result of variables affecting the
                # time step size
                potRain = time_step.do_flow(
                    surface,
                    subsurface,
                    delta_t,
                    flowControl,
                    courant)

                # stores current time step
                delta_t_tmp = delta_t

                # update time step size if necessary (based on the courant
                # condition)
                delta_t, flowControl.ratio = courant.courant(
                    potRain, delta_t, Gl.dx, flowControl.ratio)

                # I courant conditions is satisfied (time step did change) the
                # iteration loop breaks
                if (delta_t_tmp == delta_t) and (flowControl.compare_ratio()):
                    break

            # Calculate actual rainfall and adds up interception
            # todo: AP - actual is not storred in hydrographs
            actRain = time_step.do_next_h(
                surface,
                subsurface,
                rain_arr,
                cumulative,
                hydrographs,
                flowControl,
                courant,
                potRain,
                delta_t)

            # if the iteration exceed the maximal amount of iteration
            # last results are stored in hydrographs
            # and error is raised
            if not(flowControl.max_iter_reached()):
                for i in Gl.rr:
                    for j in Gl.rc[i]:
                        hydrographs.write_hydrographs_record(
                            i,
                            j,
                            flowControl,
                            courant,
                            delta_t,
                            surface,
                            subsurface,
                            curr_rain)
                post_proc.do(cumulative, Gl.mat_slope, Gl, surface.arr)
                raise MaxIterationExceeded(maxIter, total_time)

            # adjusts the last time step size
            if (Gl.end_time - flowControl.total_time) < delta_t and (Gl.end_time - flowControl.total_time) > 0:
                delta_t = Gl.end_time - flowControl.total_time

            # proceed to next time
            flowControl.update_total_time(delta_t)

            # if end time reached the main loop breaks
            if (flowControl.total_time == Gl.end_time):
                break

            timeperc = 100 * (flowControl.total_time + delta_t) / Gl.end_time
            progress_bar.pb.update(
                timeperc,
                delta_t,
                flowControl.iter_,
                flowControl.total_time +
                delta_t)

            # Calculate outflow from each reach of the stream network
            surface.stream_reach_outflow(delta_t)
            # Calculate inflow to reaches
            surface.stream_reach_inflow()
            # Record cumulative and maximal results of a reach
            surface.stream_cumulative(flowControl.total_time + delta_t)

            # set current times to previous time step
            subsurface.curr_to_pre()

            # write hydrographs of reaches
            hydrographs.write_hydrographs_record(
                i,
                j,
                flowControl,
                courant,
                delta_t,
                surface,
                subsurface,
                actRain,
                True)

            # print raster results in given time steps
            times_prt.prt(flowControl.total_time, delta_t, surface)

            # set current time results to previous time step
            # check if rill flow occur
            for i in Gl.rr:
                for j in Gl.rc[i]:

                    if surface.arr[i][j].state == 0:
                        if surface.arr[i][j].h_total_new > surface.arr[i][j].h_crit:
                            surface.arr[i][j].state = 1

                    if surface.arr[i][j].state == 1:
                        if surface.arr[i][j].h_total_new < surface.arr[i][j].h_total_pre:
                            surface.arr[i][j].h_last_state1 = surface.arr[
                                i][j].h_total_pre
                            surface.arr[i][j].state = 2

                    if surface.arr[i][j].state == 2:
                        if surface.arr[i][j].h_total_new > surface.arr[i][j].h_last_state1:
                            surface.arr[i][j].state = 1

                    surface.arr[i][j].h_total_pre = surface.arr[
                        i][j].h_total_new

        #
        # End of main loop                 ###########
        #

        prt.message("Saving data..")

        prt.message("")
        prt.message(
            "-----------------------------------------------------------")
        prt.message('Total computing time: ', str(time.time() - start))

        post_proc.do(cumulative, Gl.mat_slope, Gl, surface.arr)

        # tools.make_sur_raster(surface.arr,Globals,total_time+delta_t,output)
        # tools.make_sub_raster(subsurface.arr,Globals,total_time+delta_t,output)

        post_proc.stream_table(Gl.outdir + os.sep, surface, Gl.tokyLoc)

        hydrographs.closeHydrographs()
        prt.message("")

        import platform
        if platform.system() == "Linux":
            pid = os.getpid()
            prt.message("/proc/" + str(pid) + "/status", 'reading')
            with open("/proc/" + str(pid) + "/status", 'r') as fp:
                for i, line in enumerate(fp):
                    if i >= 11 and i <= 23:
                        prt.message(line.replace("\n", ""))
