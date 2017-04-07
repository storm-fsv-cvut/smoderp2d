#!/usr/bin/python


## \mainpage
#  Documentation of Smoderp, distributed event-based model for surface and subsurface runoff and erosion\n
# team members Petr Kavka, Karel Vrána and Jakum Jeřábek \n
# model was bild in cooperation with eng. students (Jan Zajíček, Nikola Němcová, Tomáš Edlman, Martin Neumann)
#  \n
#  The computational options are as follows:
#  - Type of flow
#    - surface
#    - subsurface
#    - surface + subsurface
#  - Flow direction algorithm
#    - D8 (default)
#    - multi-flow direction
#  - Erosion
#    - none
#    - sheet erosion
#    - sheet erosion + rill erosion
#  - Stream
#    - yes
#    - no




## @package main resolves some input variables and start the computing 
#  
#  The computing itself is performed in main_src.runoff




import sys
import os
import platform
from    main_src.tools.tools import logical_argv
from    main_src.tools.tools import get_argv
import  main_src.constants   as constants

'''
onlyshallowsurface
shallowandrillsurface
diffuseshallowsurface
shallowrillstreamsurface
surfaceandsubsurfacestreamflow
'''

  
print "--------------------- INPUT PARAMETERS ---------------------"
for item in sys.argv:
  print item
print "--------------------- ---------------- ---------------------"; print 



#if platform.system() == "Linux" :
#  os.system('sledujproces.sh ' + str(os.getpid()) + ' smod > '+str(os.getpid())+'.txt  &' )
  


if __name__ == "__main__":
  
  logical_argv(constants.PARAMETER_ARCGIS)
  if sys.argv[constants.PARAMETER_EXTRA_OUTPUT+1] != '-' :
    logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
  if sys.argv[constants.PARAMETER_MFDA+1] != '-' :
    logical_argv(constants.PARAMETER_MFDA)
  
  
  
  #sys.argv.append(sys.path[0]+os.sep+'indata/dp_hodnebodu_hodnemaletau.save')
  #sys.argv.append(sys.path[0]+os.sep+'indata/dp_hodne_bodu_tok.save')
  #sys.argv.append(sys.path[0]+os.sep+'indata/parbunek_hodnebodu_maletau.save')
  # full - full computation
  # dpre - data_preparation
  # roff - runoff
  #sys.argv.append('roff')
  #sys.argv.append('dpre')
  #sys.argv.append('full')
  
  #sys.argv.append('false')
  #logical_argv(constants.PARAMETER_DEBUG_PRT)
  #print sys.argv[constants.PARAMETER_DEBUG_PRT+2]
  
  #jj tady se nastavuje max_delta_t
  #sys.argv.append(30.0)
  
  #print constants.PARAMETER_MAX_DELTA_T
  #sys.exit()
  
  sys.argv.append('')
  #sys.argv.append('')
  import main_src.runoff

