## @package smoderp2d.src.runoff loop of the modul
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
__date__   = "$29.12.2015 18:31:25$"

# INITIAL SETTINGS:
#
# importing system moduls
# import math
import numpy as np
import time
import os
import sys
#from   smoderp2d.src.classes_main_arrays import *
#from   smoderp2d.src.tools.resolve_partial_computing import *

# importing classes



from smoderp2d.src.main_classes.General       import Globals as Gl
from smoderp2d.src.main_classes.Vegetation    import Vegetation
from smoderp2d.src.main_classes.Surface       import Surface

from smoderp2d.src.main_classes.Subsurface    import Subsurface
from smoderp2d.src.main_classes.CumulativeMax import Cumulative
from smoderp2d.src.time_step                  import TimeStep

import smoderp2d.src.constants                 as constants
from     smoderp2d.src.courant                 import Courant
import smoderp2d.src.tools.tools               as tools
import smoderp2d.src.io_functions.post_proc    as post_proc
import smoderp2d.src.io_functions.prt          as prt
import smoderp2d.src.io_functions.progress_bar as progress_bar
from   smoderp2d.src.tools.tools           import comp_type
from   smoderp2d.src.tools.times_prt       import TimesPrt
from smoderp2d.src.tools.tools             import get_argv





def init_classes():
  
  
  
  isRill, subflow, stream, diffuse, = comp_type()


  times_prt = TimesPrt()


  infiltrationType = int(0)
  total_time = 0.0      #delta_t bacha delta_t se prepisuje nize u couranta
  tz = 0
  sum_interception = 0
  ratio = 1
  maxIter = 40


  rain_arr = Vegetation(Gl.r,Gl.c,Gl.mat_ppl,Gl.mat_pi/1000.0)


  surface = Surface(Gl.r,Gl.c,Gl.mat_reten,Gl.mat_inf_index,Gl.mat_hcrit,Gl.mat_aa,Gl.mat_b)


  if (subflow == True):
    subsurface = Subsurface(L_sub = 0.1, Ks = 0.005, vg_n = 1.5, vg_l =  0.5)
  else:
    subsurface = Subsurface()

  cumulative = Cumulative()
  
  
  
  courant = Courant()
  delta_t = courant.initial_time_step(surface)
  courant.set_time_step(delta_t)


  prt.message('Corrected time step is', delta_t, '[s]')



  import io_functions.hydrographs as wf
  points_shape = Gl.points
  if points_shape and points_shape != "#":
    hydrographs = wf.Hydrographs(Gl.array_points,Gl.outdir,Gl.mat_tok_usek,Gl.rr,Gl.rc,Gl.pixel_area)
    arcgis      = get_argv(constants.PARAMETER_ARCGIS)
    if not(arcgis):
      with open(Gl.outdir+'/points.txt', 'w') as f:
        for i in range(len(Gl.array_points)):
          f.write(str(Gl.array_points[i][0]) + ' ' + str(Gl.array_points[i][3]) + ' ' + str(Gl.array_points[i][4]) + '\n')
      f.closed
  else:
    hydrographs = wf.HydrographsPass()


  time_step = TimeStep()


  # first record hydrographs
  for i in Gl.rr:
    for j in Gl.rc[i]:
      hydrographs.write_hydrographs_record(i,j,ratio,0.0,0.0,0,delta_t,total_time,surface,subsurface,0.0)


  hydrographs.write_hydrographs_record(i,j,ratio,0.0,0.0,0,delta_t,total_time,surface,subsurface,0.0,True)



  return delta_t,  times_prt, infiltrationType, total_time, tz, sum_interception, ratio, maxIter, \
    rain_arr, surface, subsurface, cumulative, courant, hydrographs, time_step
 
 
  prt.message("--------------------- ------------------- ---------------------") 
 
  
class Runoff():

  def run(self):

    # taky se vyresi vztypbi soubory nacteni dat
    # vse se hodi do ogjektu Globals as Gl

    delta_t, times_prt, infiltrationType, total_time, tz, sum_interception, ratio, maxIter, \
    rain_arr, surface, subsurface, cumulative, courant, hydrographs, time_step = init_classes()





    i = 0
    j = 0
    start = time.time()
    prt.message('Start of computing ...')
    while ( total_time < Gl.end_time ):

        #time_step.save(surface.arr,subsurface.arr)
        tz_tmp               = tz
        sum_interception_tmp = sum_interception
        iter_                = 0



        while (iter_ < maxIter):
          #print '      dt ', delta_t
          iter_ += 1
          #time_step.undo(surface.arr,subsurface.arr)
          tz                 = tz_tmp
          sum_interception   = sum_interception_tmp
          courant.reset()
          ratio_tmp = ratio

          ratio, v_sheet, v_rill, curr_rain, tz = time_step.do_flow( Gl.rr,Gl.rc,surface, subsurface, delta_t,  Gl.mat_efect_vrst, ratio, courant, Gl.itera, total_time, tz, Gl.sr )

          delta_t_tmp = delta_t

          delta_t, ratio = courant.courant(curr_rain,delta_t,Gl.spix,ratio)



          #if (iter_ == 2): raw_input()
          if (delta_t_tmp == delta_t) and (ratio_tmp == ratio) : break



        NS, sum_interception = time_step.do_next_h(Gl.rr,Gl.rc,Gl.pixel_area,surface, subsurface, rain_arr, cumulative, hydrographs, curr_rain, courant,  total_time, delta_t, Gl.combinatIndex, Gl.NoDataValue, sum_interception, Gl.mat_efect_vrst, ratio, iter_)






        if iter_ >= maxIter :
          for i in Gl.rr:
            for j in Gl.rc[i]:
              hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,curr_rain)
          post_proc.raster_output(cumulative, Gl.mat_slope, Gl, surface.arr)
          prt.error("max iteration in time step was reached\n","\tmaxIter = ", maxIter, '\n\tpartial results are saved in ', Gl.outdir, 'directory')

        if ( Gl.end_time - total_time ) < delta_t and ( Gl.end_time - total_time ) > 0:
          delta_t = Gl.end_time - total_time

        total_time = total_time + delta_t




        if ( total_time == Gl.end_time ) : break
        timeperc = 100 * (total_time+delta_t) / Gl.end_time

        progress_bar.pb.update(timeperc,delta_t,iter_,total_time+delta_t)

        surface.stream_reach_outflow(delta_t)
        surface.stream_reach_inflow()
        surface.stream_cumulative(total_time+delta_t)

        subsurface.curr_to_pre()

        hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,curr_rain,True)


        times_prt.prt(total_time,delta_t,surface)


        for i in Gl.rr:
          for j in Gl.rc[i]:

            if surface.arr[i][j].state == 0 :
              if surface.arr[i][j].h_total_new > surface.arr[i][j].h_crit :
                surface.arr[i][j].state = 1

            if surface.arr[i][j].state == 1 :
              if surface.arr[i][j].h_total_new < surface.arr[i][j].h_total_pre :
                surface.arr[i][j].h_last_state1  = surface.arr[i][j].h_total_pre
                surface.arr[i][j].state = 2

            if surface.arr[i][j].state == 2 :
              if surface.arr[i][j].h_total_new > surface.arr[i][j].h_last_state1 :
                surface.arr[i][j].state = 1

            surface.arr[i][j].h_total_pre  = surface.arr[i][j].h_total_new



        #raw_input()

    #######################################################################
    ##########                 End of main loop                 ###########
    #######################################################################












    prt.message("Saving data..")


    prt.message("")
    prt.message("-----------------------------------------------------------")
    prt.message('Total computing time: ',str(time.time()-start))



    post_proc.do(cumulative, Gl.mat_slope, Gl, surface.arr)


    #tools.make_sur_raster(surface.arr,Globals,total_time+delta_t,output)
    #tools.make_sub_raster(subsurface.arr,Globals,total_time+delta_t,output)

    post_proc.stream_table(Gl.outdir+os.sep, surface, Gl.tokyLoc)

    hydrographs.closeHydrographs()
    prt.message("")


    import platform
    if platform.system() == "Linux" :
      pid = os.getpid()
      prt.message("/proc/"+str(pid)+"/status", 'reading...')
      with open("/proc/"+str(pid)+"/status",'r') as fp:
        for i, line in enumerate(fp):
          if i >= 11 and i <= 23 :
            prt.message(line.replace("\n",""))








