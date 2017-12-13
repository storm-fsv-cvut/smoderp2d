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




import platform




if __name__ == "__main__":
  
  # init class contains global variables
  if platform.system() == "Linux" :
    from main_src.main_classes.General import initLinux
    init = initLinux
  elif platform.system() == "Windows" :
    from main_src.main_classes.General import initWin
    init = initWin
  else :
    from main_src.main_classes.General import initNone
    init = initNone
  
  
  # returns false for dpre type of computation
  # or unsaported platform
  run = init()
  
  
  if ((run)) :
    # runoff.run() starts the computation
    from main_src.runoff import Runoff
    runoff = Runoff()
    
    runoff.run()
    
