## @package nacteni a uloze hodnot co jsou z data preparation 
#  roff, dpre, full se resi  resolve_partial_computin
#  odtud se jen vola tato funkce.


import math
import sys

# get_indata is method which reads the input data
from   main_src.tools.resolve_partial_computing import get_indata
# get type of computing identifier based on the string
from   main_src.tools.tools                     import comp_type

from   main_src.tools.tools                   import get_argv
import main_src.constants                         as constants


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
  
  
  
  
  
  
  
  
  
  
## Class Globals contains global variables 
#  
#  from data_preparation, in instance of class needed
#  the data are taken from import of this class
#
class Globals:
  ## area of a raster cell in meters
  pixel_area = None
  ## number of rows in rasters
  r        = None
  ## number of columns in rasters
  c        = None
  ## id of rows in computational domain
  rr    = None
  ## id of columns in computational domain
  rc    = None
  ## id of rows in at the boundary of computational domain
  br    = None
  ## id of columns in at the boundary of computational domain
  bc    = None
  ## x coordinate od of left bottom corner of raster
  xllcorner = None
  ## y coordinate od of left bottom corner of raster
  yllcorner = None
  ## no data value for raster
  NoDataValue = None
  ## no data integer value for raster
  NoDataInt   = None
  ## size of raster cell
  dx = None
  ## size of raster cell
  dy = None
  ## type of computation
  type_of_computing = None
  ## path to a output directory
  outdir = None
  ## raster with labeled boundary cells
  mat_boundary = None
  ## list containing coordinates of catchment outlet cells
  outletCells  = None
  ## array containing information of hydrogram points
  array_points = None
  ## combinatIndex
  combinatIndex = None
  ## time step
  delta_t = None
  ## raster contains potential interception data
  mat_pi  = None
  ## raster contains leaf area data
  mat_ppl = None
  ## raster contains surface retention data
  surface_retention = None
  ## raster contains id of infiltration type 
  mat_inf_index = None
  ## raster contains critical water level
  mat_hcrit = None
  ## raster contains parameter of power law for surface runoff
  mat_aa = None
  ## raster contains parameter of power law for surface runoff
  mat_b = None
  ## raster contains surface retention data
  mat_reten = None
  ## raster contains flow direction datas
  mat_fd = None
  ## raster contains digital elevation model
  mat_dmt = None
  ## raster contains efective couterline data
  mat_efect_vrst = None
  ## raster contains surface slopes data
  mat_slope = None
  ## raster labels not a number cells
  mat_nan = None
  ## raster contains parameters ...
  mat_a = None
  ## raster contains parameters ...
  mat_n = None
  ## ???
  points = None
  ## ???
  poradi = None
  ## end time of computation
  end_time = None
  ## ???
  spix = None
  ## raster contains cell flow state information
  state_cell = None
  ## path to directory for temporal data storage
  temp = None
  ## ???
  vpix = None
  ## bool variable for flow direction algorithm (false=one direction, true multiple flow direction)
  mfda = None
  ## list contains the precipitation data
  sr = None
  ## counter of precipitation intervals
  itera = None
  ## ???
  toky = None
  ## ???
  cell_stream = None
  ## raster contains the reach id data
  mat_tok_usek = None
  ## ???
  STREAM_RATIO = None
  ## ???
  tokyLoc = None





## Init fills the Globals class with values from preprocessing 
# 
def initLinux():
  
  
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('typecomp', help='type of computation', type=str, choices=['full','dpre','roff'])
  parser.add_argument('--indata', help='file with input data', type=str)
  args = parser.parse_args()
  partial_comp = args.typecomp

  
  
  if (partial_comp == 'roff') :
    
    
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
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = get_indata(partial_comp,args)
  
    
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
    
    return True
  
  else:
    print 'for Linux only roff'
    return False
  
  
  
  
  
  
  
  
## Init fills the Globals class with values from preprocessing 
# 
def initWin():
  

  sys.argv.append('outdata.save')
  sys.argv.append('full')
  sys.argv.append(False)
  sys.argv.append('-')
  partial_comp = get_argv(constants.PARAMETER_PARTIAL_COMPUTING)


  
  
  if (partial_comp == 'roff') | (partial_comp == 'full') :
    
    
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
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = get_indata(partial_comp,sys.argv)
    
    
    
    
    
    
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
    
    return True
  
  elif (partial_comp == 'dprea') :
    stop = get_indata(partial_comp,args)
    return stop
  
  
  
  
  
  
  
  
  
  
def initNone():
  print "Unsupported platform."
  print "Exiting smoderp 2d..."
  return False










