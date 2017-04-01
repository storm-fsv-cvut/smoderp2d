import os 


import main_src.constants                         as constants
from   main_src.tools.tools                   import get_argv
from   main_src.tools.tools                   import set_argv
from   main_src.tools.tools                   import prt_sys_argv
from   main_src.tools.tools                   import int_comp_type
from   main_src.tools.tools                   import int_comp_type


# # # # # # # # # # # # # # # # # # # # # # #
#from inspect import currentframe, getframeinfo
#frameinfo = getframeinfo(currentframe())
# # # # # # # # # # # # # # # # # # # # # # #

partial_comp = get_argv(constants.PARAMETER_PARTIAL_COMPUTING)


if partial_comp == 'full':
  from main_src.data_preparation import *

elif partial_comp == 'dpre':
  
  from    main_src.data_preparation    import *
  import  main_src.tools.save_load_data    as sld
  #import  main_src.tools.save_load_data_nopickle    as sld   # preparate
  
  dataList = [boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate,\
    NoDataValue, array_points, \
    cols, rows, combinatIndex, delta_t,  \
    mat_pi, mat_ppl, \
    surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b,\
    mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
    mat_a,   \
    mat_n,   \
    output, pixel_area, points, poradi,  end_time, spix, state_cell, \
    temp, type_of_computing, vpix, mfda, sr, itera, \
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc]
  
  
  sld.save_data(dataList,get_argv(constants.PARAMETER_INDATA))
  #sld.save(dataList,get_argv(constants.PARAMETER_INDATA))    #   preparated
  
  
  sys.exit('data prepared...')
  

elif partial_comp == 'roff':
  import  main_src.tools.save_load_data as sld
  import main_src.processes.rainfall    as rainfall
  #import  main_src.tools.save_load_data_nopickle    as sld   # preparated
  
  
  indata = get_argv(constants.PARAMETER_INDATA)

  boundaryRows, boundaryCols, \
  mat_boundary, rrows, rcols, outletCells, \
  x_coordinate, y_coordinate,\
  NoDataValue, array_points, \
  cols, rows, combinatIndex, delta_t,  \
  mat_pi, mat_ppl, \
  surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b,\
  mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
  mat_a,   \
  mat_n,   \
  output, pixel_area, points, poradi,  end_time, spix, state_cell, \
  temp, type_of_computing, vpix, mfda, sr, itera, \
  toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load_data(indata)


  """
  boundaryRows, boundaryCols, \
  mat_boundary, rrows, rcols, outletCells, \
  x_coordinate, y_coordinate,\
  NoDataValue, array_points, \
  cols, rows, combinatIndex, delta_t,  \
  mat_pi, mat_ppl, \
  surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b,\
  mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
  mat_a,   \
  mat_n,   \
  output, pixel_area, points, poradi,  end_time, spix, state_cell, \
  temp, type_of_computing, vpix, mfda, sr, itera, \
  toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load(indata)   #preparated
  """


  if get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY) == '-':
    set_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY, output)
    
  if get_argv(constants.PARAMETER_END_TIME) == '-':
    set_argv(constants.PARAMETER_END_TIME, end_time)  
  
  if get_argv(constants.PARAMETER_MFDA) == '-':
    set_argv(constants.PARAMETER_MFDA,mfda)
    
  if get_argv(constants.PARAMETER_SURFACE_RETENTION) == '-':
    set_argv(constants.PARAMETER_SURFACE_RETENTION,surface_retention)
  
  if get_argv(constants.PARAMETER_TYPE_COMPUTING) == '-':
    set_argv(constants.PARAMETER_TYPE_COMPUTING,int_comp_type(type_of_computing))
  
  
  #jj end time se musi takto delta vzdy, neni v save
  output = get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)
  end_time = float(get_argv(constants.PARAMETER_END_TIME))*60.0
  mfda                    = get_argv(constants.PARAMETER_MFDA)
  surface_retention       = float(get_argv(constants.PARAMETER_SURFACE_RETENTION))/1000 #prevod z [mm] na [m]
  
  
  
  arcgis                  = get_argv(constants.PARAMETER_ARCGIS)
  
  
  # ponechani deste z save
  rainfall_file_path      = get_argv(constants.PARAMETER_PATH_TO_RAINFALL_FILE)
  if rainfall_file_path == '-' :
    pass
  # zmena deste posave, pokud se pocita jen roff
  else:
    sr,itera  = rainfall.load_precipitation(rainfall_file_path)
  
  

  if os.path.exists(output):
    import shutil
    shutil.rmtree(output)
  if not os.path.exists(output):
    os.makedirs(output)
    #os.makedirs(output+os.sep+'prubeh')
    
  print '--------- po nacteni z save ---------'    
  prt_sys_argv()
  print '--------- ---------- - ---- ---------'    