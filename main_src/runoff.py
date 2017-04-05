## @package main_src.runoff loop of the modul
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

__author__="edlman"
__date__ ="$29.12.2015 18:31:25$"

#INITIAL SETTINGS:
#
# importing system moduls
#import math
import numpy as np
import time
import os
import sys
#from   main_src.classes_main_arrays import *
#from   main_src.tools.resolve_partial_computing import *

# importing classes
from main_src.time_step                  import TimeStep
from main_src.main_classes.General       import *
from main_src.main_classes.Vegetation    import Vegetation
from main_src.main_classes.Surface       import Surface
from main_src.main_classes.Subsurface    import Subsurface
from main_src.main_classes.CumulativeMax import Cumulative


import main_src.constants                 as constants
import main_src.courant                   as courant
import main_src.tools.tools               as tools
import main_src.io_functions.post_proc    as post_proc
import main_src.io_functions.prt          as prt
import main_src.io_functions.progress_bar as progress_bar
from   main_src.tools.tools           import comp_type
from   main_src.tools.times_prt       import TimesPrt



isRill, subflow, stream, diffuse = comp_type()






times_prt = TimesPrt()





start = time.time()

infiltrationType = int(0)
total_time = 0.0      #delta_t bacha delta_t se prepisuje nize u couranta
tz = 0
sum_interception = 0
ratio = 1
maxIter = 40



rain_arr = Vegetation(mat_ppl,mat_pi/1000.0)
mat_ppl = None; del mat_ppl
mat_pi = None; del mat_pi



surface = Surface(-surface_retention,mat_inf_index,mat_hcrit,mat_aa,mat_b)
mat_inf_index = None; del mat_inf_index
mat_hcrit = None; del mat_hcrit
mat_aa = None; del mat_aa
mat_b = None; del mat_b


if (subflow == True):
  subsurface = Subsurface(L_sub = 0.1, Ks = 0.005, vg_n = 1.5, vg_l =  0.5)
else:
  subsurface = Subsurface()



cumulative = Cumulative()



prt.message("--------------------- ------------------- ---------------------")





courant = courant.Courant()
delta_t = courant.initial_time_step(surface)
courant.set_time_step(delta_t)


prt.message('Corrected time step is', delta_t, '[s]')



import io_functions.hydrographs as wf
points_shape = points
if points_shape and points_shape != "#":
  hydrographs = wf.Hydrographs(array_points,output,mat_tok_usek,Globals)
  arcgis      = get_argv(constants.PARAMETER_ARCGIS)
  if not(arcgis):
    with open(output+'/points.txt', 'w') as f:
      for i in range(len(array_points)):
        f.write(str(array_points[i][0]) + ' ' + str(array_points[i][3]) + ' ' + str(array_points[i][4]) + '\n')
    f.closed
else:
  hydrographs = wf.HydrographsPass()


time_step = TimeStep()


# first record hydrographs
for i in rrows:
  for j in rcols[i]:
    hydrographs.write_hydrographs_record(i,j,ratio,0.0,0.0,0,delta_t,total_time,surface,subsurface,0.0,)


hydrographs.write_hydrographs_record(i,j,ratio,0.0,0.0,0,delta_t,total_time,surface,subsurface,0.0,True)








while ( total_time < end_time ):

    #time_step.save(surface.arr,subsurface.arr)
    tz_tmp               = tz
    sum_interception_tmp = sum_interception
    iter_                = 0
    
    
    
    while (iter_ < maxIter):
      iter_ += 1
      #time_step.undo(surface.arr,subsurface.arr)
      tz                 = tz_tmp
      sum_interception   = sum_interception_tmp
      courant.reset()
      ratio_tmp = ratio

      
      ratio, v_sheet, v_rill, curr_rain, tz = time_step.do_flow( surface, subsurface, delta_t, Globals, mat_efect_vrst, ratio, courant, itera, total_time, tz, sr )

      delta_t_tmp = delta_t

      delta_t, ratio = courant.courant(curr_rain,delta_t,spix,ratio)
      
      

      if (delta_t_tmp == delta_t) and (ratio_tmp == ratio) : break
    
    
    
    
    NS, sum_interception = time_step.do_next_h(surface, subsurface, rain_arr, cumulative, hydrographs, curr_rain, courant, Globals, total_time, delta_t, combinatIndex, NoDataValue, sum_interception, mat_efect_vrst, ratio, iter_)
    
    
    timeperc = 100 * (total_time+delta_t) / end_time
    #raw_input()
  
    progress_bar.pb.update(timeperc,delta_t,iter_,total_time+delta_t)





    
    if iter_ >= maxIter :
      for i in rrows:
        for j in rcols[i]:
          hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,curr_rain)
      post_proc.raster_output(output, cumulative, mat_slope, Globals, surface.arr)
      prt.error("max iteration in time step was reached\n","\tmaxIter = ", maxIter, '\n\tpartial results are saved in ', output, 'directory')


    surface.stream_reach_outflow(delta_t)
    surface.stream_reach_inflow()
    surface.stream_cumulative(total_time+delta_t)
    
    
    for i in rrows:
      for j in rcols[i]:
        if surface.arr[i][j].state == 0 :
          if surface.arr[i][j].h_total_new > surface.arr[i][j].h_crit :
            surface.arr[i][j].state = 1
        if surface.arr[i][j].state == 1 : 
          if surface.arr[i][j].h_total_new < surface.arr[i][j].h_total_pre : 
            surface.arr[i][j].state = 2
          
        surface.arr[i][j].h_total_pre  = surface.arr[i][j].h_total_new
        


    subsurface.curr_to_pre()

    hydrographs.write_hydrographs_record(i,j,ratio,courant.cour_most,courant.cour_most_rill,iter_,delta_t,total_time+delta_t,surface,subsurface,curr_rain,True)
    
    
    times_prt.prt(total_time,delta_t,surface)
 
    if ( end_time - total_time ) < delta_t and ( end_time - total_time ) > 0:
      delta_t = end_time - total_time

    total_time = total_time + delta_t
    #raw_input()

#######################################################################
##########                 End of main loop                 ###########
#######################################################################











prt.message("Saving data..")

 
prt.message("")
prt.message("-----------------------------------------------------------")
prt.message('Total computing time: ',str(time.time()-start))



post_proc.raster_output(output, cumulative, mat_slope, Globals, surface.arr)



#tools.make_sur_raster(surface.arr,Globals,total_time+delta_t,output)
#tools.make_sub_raster(subsurface.arr,Globals,total_time+delta_t,output)

post_proc.stream_table(output+os.sep, surface, tokyLoc)

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








