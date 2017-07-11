## nacteni a uloze hodnot co jsou z data preparation 
#  roff, dpre, full se resi  resolve_partial_computin
#  odtud se jen vola tato funkce.


import math

from   main_src.tools.resolve_partial_computing import get_indata
from   main_src.tools.tools                     import comp_type



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
  pixel_area = None
  r        = None
  c        = None
  rr    = None
  rc    = None
  br    = None
  bc    = None
  xllcorner = None
  yllcorner = None
  NoDataValue = None
  NoDataInt   = None
  dx = None
  dy = None
  type_of_computing = None
  outdir = None
  mat_boundary = None
  outletCells  = None
  array_points = None
  combinatIndex = None
  delta_t = None
  mat_pi  = None
  mat_ppl = None
  surface_retention = None
  mat_inf_index = None
  mat_hcrit = None
  mat_aa = None
  mat_b = None
  mat_reten = None
  mat_fd = None
  mat_dmt = None
  mat_efect_vrst = None
  mat_slope = None
  mat_nan = None
  mat_a = None
  mat_n = None
  points = None
  poradi = None
  end_time = None
  spix = None
  state_cell = None
  temp = None
  vpix = None
  mfda = None
  sr = None
  itera = None
  toky = None
  cell_stream = None
  mat_tok_usek = None
  STREAM_RATIO = None
  tokyLoc = None


def init():

  boundaryRows, boundaryCols, \
  mat_boundary, rrows, rcols, outletCells, \
  x_coordinate, y_coordinate,\
  NoDataValue, array_points, \
  cols, rows, combinatIndex, delta_t,  \
  mat_pi, mat_ppl, \
  surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
  mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
  mat_a,   \
  mat_n,   \
  output, pixel_area, points, poradi,  end_time, spix, state_cell, \
  temp, type_of_computing, vpix, mfda, sr, itera, \
  toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = get_indata()

  
  
  Globals.pixel_area = pixel_area
  Globals.r        = rows
  Globals.c        = cols
  Globals.rr    = rrows
  Globals.rc    = rcols
  Globals.br    = boundaryRows
  Globals.bc    = boundaryCols
  Globals.xllcorner = x_coordinate
  Globals.yllcorner = y_coordinate
  Globals.NoDataValue = NoDataValue
  Globals.NoDataInt   = int(-9999)
  Globals.dx = math.sqrt(pixel_area)
  Globals.dy = Globals.dx
  Globals.type_of_computing = type_of_computing
  Globals.outdir = output
  Globals.mat_boundary = mat_boundary
  Globals.outletCells  = outletCells
  Globals.array_points = array_points
  Globals.combinatIndex = combinatIndex
  Globals.mat_pi  = mat_pi
  Globals.mat_ppl = mat_ppl
  Globals.surface_retention = surface_retention
  Globals.mat_inf_index = mat_inf_index
  Globals.mat_hcrit = mat_hcrit
  Globals.mat_aa = mat_aa
  Globals.mat_b = mat_b
  Globals.mat_reten = mat_reten
  Globals.mat_fd = mat_fd
  Globals.mat_dmt = mat_dmt
  Globals.mat_efect_vrst = mat_efect_vrst
  Globals.mat_slope = mat_slope
  Globals.mat_nan = mat_nan
  Globals.mat_a = mat_a
  Globals.mat_n = mat_n
  Globals.points = points
  Globals.poradi = poradi
  Globals.end_time = end_time
  Globals.spix = spix
  Globals.state_cell = state_cell
  Globals.temp = temp
  Globals.vpix = vpix
  Globals.mfda = mfda
  Globals.sr = sr
  Globals.itera = itera 
  Globals.toky = toky
  Globals.cell_stream = cell_stream
  Globals.mat_tok_usek = mat_tok_usek 
  Globals.STREAM_RATIO = STREAM_RATIO
  Globals.tokyLoc = tokyLoc
  Globals.diffuse = comp_type('diffuse')
  Globals.subflow = comp_type('subflow')
  
  
  
  
  
  
  
  
  
  