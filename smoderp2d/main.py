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




## @package smoderp2d.main resolves some input variables and start the computing
#
#  The computing itself is performed in main_src.runoff








##### to do list

# main.py by se asi podle konvenci mel jmenovat smodepr.py
# mal by tam byl setup.py

##### 


def run() :
  

  import smoderp2d.src.io_functions.prttxtlogo
  
  import platform
  # init class contains global variables
  if platform.system() == "Linux" :
    from smoderp2d.src.main_classes.General import initLinux
    init = initLinux
  elif platform.system() == "Windows" :
    import sys
    from smoderp2d.src.main_classes.General import initWin
    init = initWin
    sys.argv.append('#')               #  mfda
    sys.argv.append(False)             #  extra output
    sys.argv.append('outdata.save')    #  in data
    sys.argv.append('full')            #  castence nee v arcgis
    sys.argv.append(False)             #  debug print
    sys.argv.append('-')               # print times
  else :
    from smoderp2d.src.main_classes.General import initNone
    init = initNone
  
  
  # returns false for dpre type of computation
  # or unsaported platform
  ok = init()
  
  
  if ((ok)) :
    # runoff.run() starts the computation
    from smoderp2d.src.runoff import Runoff
    runoff = Runoff()
    
    runoff.run()





if __name__ == "__main__":
  
    
    
    run()
