## @package nacteni a uloze hodnot co jsou z data preparation
#  roff, dpre, full se resi  resolve_partial_computin
#  odtud se jen vola tato funkce.


import math
import sys

# get_indata is method which reads the input data
from   smoderp2d.src.tools.resolve_partial_computing import get_indata
# get type of computing identifier based on the string
from   smoderp2d.src.tools.tools                     import comp_type

from   smoderp2d.src.tools.tools                   import get_argv
import smoderp2d.src.constants                         as constants


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

  def get_pixel_area(self):
    return self.pixel_area
  
  def get_rows(self):
    return self.r
  
  def get_cols(self):
    return self.c
  
  def get_rrows(self):
    return self.rr
  
  def get_bor_rows(self):
    return self.br
  
  def get_bor_cols(self):
    return self.bc
  
  def get_xllcorner (self):
    return self.xllcorner
  
  def get_yllcorner(self):
    return self.yllcorner
  
  def get_NoDataValue(self):
    return self.NoDataValue
  
  def get_NoDataInt(self):
    return self.NoDataInt
  
  def get_dx(self):
    return self.dx
  
  def get_dy(self):
    return self.dy
  
  def get_type_of_computing(self):
    return self.type_of_computing
  
  def get_outdir(self):
    return self.outdir
  
  def get_mat_boundary(self):
    return self.mat_boundary
  
  def get_outletCells(self):
    return self.outletCells
  
  def get_array_points(self):
    return self.array_points
  
  def get_combinatIndex(self):
    return self.combinatIndex
  
  def get_delta_t(self):
    return self.delta_t
  
  
  def get_mat_pi(self):
    return self.mat_pi
  
  
  def get_mat_ppl(self):
    return self.mat_ppl
  
  
  def get_surface_retention(self):
    return self.surface_retention
  
  
  def get_mat_inf_index(self):
    return self.mat_inf_index
  
  
  def get_mat_hcrit(self):
    return self._mat_hcrit
  
  def get_mat_aa(self):
    return self.mat_aa
  
  def get_mat_b(self):
    return self.mat_b
  
  def get_mat_reten(self):
    return self.mat_reten
  
  def get_mat_fd(self):
    return self.mat_fd
  
  def get_mat_dmt(self):
    return self.mat_dmt
  
  def get_mat_efect_vrst(self):
    return self.mat_efect_vrst
  
  def get_mat_slope(self):
    return self.mat_slope
  
  def get_mat_nan(self):
    return self.mat_nan
  
  def get_mat_a(self):
    return self.mat_a
  
  def get_mat_n(self):
    return self.mat_n
  
  def get_points(self):
    return self.points
  
  def get_poradi(self):
    return self.poradi
  
  def get_end_tim(self):
    return self.end_time
  
  def get_spix(self):
    return self.spix
  
  def get_state_cell(self):
    return self.state_cell
  
  def get_temp(self):
    return self.temp
  
  def get_vpix(self):
    return self.vpix
  
  def get_mfda(self):
    return self.mfda
  
  def get_sr(self):
    return self.sr
  
  def get_itera(self):
    return self.itera
  
  def get_toky(self):
    return self.toky
  
  def get_cell_stream(self):
    return self.cell_stream
  
  def get_mat_tok_usek(self):
    return self.mat_tok_usek
  
  def get_STREAM_RATIO(self):
    return self.STREAM_RATIO
  
  def get_tokyLoc(self):
    return self.tokyLoc
  
  
  
    



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


    sys.argv.append(type_of_computing)



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

  elif (partial_comp == 'dpre') :
    stop = get_indata(partial_comp,sys.argv)
    return stop










def initNone():
  print "Unsupported platform."
  print "Exiting smoderp 2d..."
  return False










