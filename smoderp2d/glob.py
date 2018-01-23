## @package smoderp2d.glob
#  Contains the global variables provided by preprocessing


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





def set_pixel_area(val):
  global pixel_area
  pixel_area = val
  
  
def set_rows(val):
  global r
  r = val

def set_cols(val):
  global c
  c = val

def set_rrows(val):
  global rr
  rr = val

def set_bor_rows(val):
  global br
  br = val

def set_bor_cols(val):
  global bc
  bc = val

def set_xllcorner (val):
  global xllcorner
  xllcorner = val

def set_yllcorner(val):
  global yllcorner
  yllcorner = val

def set_NoDataValue(val):
  global NoDataValue
  NoDataValue = val

def set_NoDataInt(val):
  global NoDataInt
  NoDataInt = val

def set_dx(val):
  global dx
  dx = val

def set_dy(val):
  global dy
  dy = val

def set_type_of_computing(val):
  global type_of_computing
  type_of_computing = val

def set_outdir(val):
  global outdir
  outdir = val

def set_mat_boundary(val):
  global mat_boundary
  mat_boundary = val

def set_outletCells(val):
  global outletCells
  outletCells = val

def set_array_points(val):
  global array_points
  array_points = val

def set_combinatIndex(val):
  global combinatIndex
  combinatIndex = val

def set_delta_t(val):
  global delta_t
  delta_t = val

def set_mat_pi(val):
  global mat_pi
  mat_pi = val

def set_mat_ppl(val):
  global mat_ppl
  mat_ppl = val

def set_surface_retention(val):
  global surface_retention
  surface_retention = val

def set_mat_inf_index(val):
  global mat_inf_index
  mat_inf_index = val

def set_mat_hcrit(val):
  global mat_hcrit
  mat_hcrit = val

def set_mat_aa(val):
  global mat_aa
  mat_aa = val

def set_mat_b(val):
  global mat_b
  mat_b = val

def set_mat_reten(val):
  global mat_reten
  mat_reten = val

def set_mat_fd(val):
  global mat_fd
  mat_fd = val

def set_mat_dmt(val):
  global mat_dmt
  mat_dmt = val

def set_mat_efect_vrst(val):
  global mat_efect_vrst
  mat_efect_vrst = val

def set_mat_slope(val):
  global mat_slope
  mat_slope = val

def set_mat_nan(val):
  global mat_nan
  mat_nan = val

def set_mat_a(val):
  global mat_a
  mat_a = val

def set_mat_n(val):
  global mat_n
  mat_n = val

def set_points(val):
  global points
  points = val

def set_poradi(val):
  global poradi
  poradi = val

def set_end_tim(val):
  global end_time
  end_time = val

def set_spix(val):
  global spix
  spix = val

def set_state_cell(val):
  global state_cell
  state_cell = val

def set_temp(val):
  global temp
  temp = val

def set_vpix(val):
  global vpix
  vpix = val

def set_mfda(val):
  global mfda
  mfda = val

def set_sr(val):
  global sr
  sr = val

def set_itera(val):
  global itera
  itera = val

def set_toky(val):
  global toky
  toky = val

def set_cell_stream(val):
  global cell_stream
  cell_stream = val

def set_mat_tok_usek(val):
  global mat_tok_usek
  mat_tok_usek = val

def set_STREAM_RATIO(val):
  global STREAM_RATIO
  STREAM_RATIO = val

def set_tokyLoc(val):
  global tokyLoc
  tokyLoc = val

















def get_pixel_area():
  return pixel_area

def get_rows():
  return r

def get_cols():
  return c

def get_rrows():
  return rr

def get_bor_rows():
  return br

def get_bor_cols():
  return bc

def get_xllcorner ():
  return xllcorner

def get_yllcorner():
  return yllcorner

def get_NoDataValue():
  return NoDataValue

def get_NoDataInt():
  return NoDataInt

def get_dx():
  return dx

def get_dy():
  return dy

def get_type_of_computing():
  return type_of_computing

def get_outdir():
  return outdir

def get_mat_boundary():
  return mat_boundary

def get_outletCells():
  return outletCells

def get_array_points():
  return array_points

def get_combinatIndex():
  return combinatIndex

def get_delta_t():
  return delta_t

def get_mat_pi():
  return mat_pi

def get_mat_ppl():
  return mat_ppl

def get_surface_retention():
  return surface_retention

def get_mat_inf_index():
  return mat_inf_index

def get_mat_hcrit():
  return mat_hcrit

def get_mat_aa():
  return mat_aa

def get_mat_b():
  return mat_b

def get_mat_reten():
  return mat_reten

def get_mat_fd():
  return mat_fd

def get_mat_dmt():
  return mat_dmt

def get_mat_efect_vrst():
  return mat_efect_vrst

def get_mat_slope():
  return mat_slope

def get_mat_nan():
  return mat_nan

def get_mat_a():
  return mat_a

def get_mat_n():
  return mat_n

def get_points():
  return points

def get_poradi():
  return poradi

def get_end_tim():
  return end_time

def get_spix():
  return spix

def get_state_cell():
  return state_cell

def get_temp():
  return temp

def get_vpix():
  return vpix

def get_mfda():
  return mfda

def get_sr():
  return sr

def get_itera():
  return itera

def get_toky():
  return toky

def get_cell_stream():
  return cell_stream

def get_mat_tok_usek():
  return mat_tok_usek

def get_STREAM_RATIO():
  return STREAM_RATIO

def get_tokyLoc():
  return tokyLoc









