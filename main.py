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




if __name__ == "__main__":
  
  
  # init class contains global variables
  from main_src.main_classes.General import init
  
  # in case of dpre type of computation 
  # false is returnde and no model is run
  run = init()

  
  if ((run)) :
    # runoff.run() starts the computation
    from main_src.runoff import Runoff
    runoff = Runoff()
    
    runoff.run()
    

  
  
  
  
  
  
  
  
  
  
  
  

