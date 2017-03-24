import math

from   main_src.tools.resolve_partial_computing import *


## Documentation for a class.
#
#  method to compute size of class arrays
class Size:

  ## size
  #  @param arrayNBytes <numpy array>.nbytes
  #  @param m value in denominator to get bytes, kilobytes (m=2**10), megabytes (m=2**10+m**10) and so on.
  def size(self, arrayNBytes, m=1.0):
    # arrayNBytes eq self.state.nbytes
    size = (self.n * arrayNBytes)/m
    return size
  
  
  
class Globals:
  pixel_area = pixel_area
  r        = rows
  c        = cols
  rr    = rrows
  rc    = rcols
  br    = boundaryRows
  bc    = boundaryCols
  xllcorner = x_coordinate
  yllcorner = y_coordinate
  NoDataValue = NoDataValue
  NoDataInt   = int(-9999)
  dx = math.sqrt(pixel_area)
  dy = dx
  type_of_computing = type_of_computing
  outdir = output