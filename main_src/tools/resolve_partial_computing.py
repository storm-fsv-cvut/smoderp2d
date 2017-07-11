import os 
import sys



import main_src.constants                         as constants
from   main_src.tools.tools                   import get_argv
from   main_src.tools.tools                   import set_argv
from   main_src.tools.tools                   import prt_sys_argv
from   main_src.tools.tools                   import int_comp_type
from   main_src.tools.tools                   import int_comp_type
from    main_src.tools.tools                  import logical_argv


# # # # # # # # # # # # # # # # # # # # # # #
#from inspect import currentframe, getframeinfo
#frameinfo = getframeinfo(currentframe())
# # # # # # # # # # # # # # # # # # # # # # #



def get_indata ():
  
  try:
    partial_comp = get_argv(constants.PARAMETER_PARTIAL_COMPUTING)
  except IndexError:
    partial_comp = 'roff'

  if partial_comp == 'full':
    from main_src.data_preparation import prepare_data


    return  prepare_data(sys.argv)

    




  elif partial_comp == 'dpre':
    
    from main_src.data_preparation import prepare_data
    import  main_src.tools.save_load_data    as sld
    
    
    boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate,\
        NoDataValue, array_points, \
        cols, rows, combinatIndex, delta_t,  \
        mat_pi, mat_ppl, \
        surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten, \
        mat_fd, mat_dmt, mat_efect_vrst, mat_slope, mat_nan, \
        mat_a,   \
        mat_n,   \
        output, pixel_area, points, poradi,  end_time, spix, state_cell, \
        temp, type_of_computing, vpix, mfda, sr, itera, \
        toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = prepare_data(sys.argv)
    
    
    
    
    #import  main_src.tools.save_load_data_nopickle    as sld   # preparate
    
    dataList = [boundaryRows, boundaryCols, mat_boundary, rrows, rcols, outletCells, x_coordinate, y_coordinate,\
      NoDataValue, array_points, \
      cols, rows, combinatIndex, delta_t,  \
      mat_pi, mat_ppl, \
      surface_retention, mat_inf_index, mat_hcrit, mat_aa, mat_b, mat_reten,\
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

    import argparse
    import ConfigParser
    
    # to je to je jen provizorne, pokud to bude petr delat tak jo doposud 
    if len(sys.argv) > 7 :
      logical_argv(constants.PARAMETER_ARCGIS)
      logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
      logical_argv(constants.PARAMETER_MFDA)
      indata = get_argv(constants.PARAMETER_INDATA)
    else:
      parser = argparse.ArgumentParser(prog='Smoderp 0.1');
      parser.add_argument('-s', '--sort', nargs =1, action = 'store', choices = ['roff', 'dpre','full'], default='mcs', help='Type of computing')
      parser.add_argument('--indata', nargs ='+', action = 'store', help='Parameter file')

      args = parser.parse_args()
      
      
      Config = ConfigParser.ConfigParser()
      Config.read(args.indata[0])
      sys.argv = [sys.argv.pop(0)]
      #print sys.argv
      sys.argv.append(Config.get('GIS','dem'))
      sys.argv.append(Config.get('GIS','soil'))
      sys.argv.append(Config.get('shape atr','soil-atr'))
      sys.argv.append(Config.get('GIS','lu'))
      sys.argv.append(Config.get('shape atr','lu-atr'))
      sys.argv.append(Config.get('srazka','file'))
      sys.argv.append(Config.get('time','maxdt'))
      sys.argv.append(Config.get('time','endtime'))
      sys.argv.append(Config.get('Other','reten'))
      sys.argv.append(Config.get('Other','points'))
      sys.argv.append(Config.get('Other','outdir'))
      sys.argv.append(Config.get('Other','typecomp'))
      sys.argv.append(Config.get('Other','mfda'))
      sys.argv.append(Config.get('Other','soilvegtab'))
      sys.argv.append(Config.get('Other','soilvegcode'))
      sys.argv.append(Config.get('Other','streamshp'))
      sys.argv.append(Config.get('Other','streamtab'))
      sys.argv.append(Config.get('Other','streamtabcode'))
      sys.argv.append(Config.get('Other','arcgis'))
      sys.argv.append(Config.get('Other','extraout'))
      sys.argv.append(Config.get('Other','indata'))
      sys.argv.append(Config.get('Other','partialcomp'))
      sys.argv.append(Config.get('Other','debugprt'))
      sys.argv.append(Config.get('Other','printtimes'))
      
      logical_argv(constants.PARAMETER_ARCGIS)
      logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
      logical_argv(constants.PARAMETER_MFDA)
      indata = get_argv(constants.PARAMETER_INDATA)    

    import main_src.tools.save_load_data as sld
    import main_src.processes.rainfall    as rainfall
    #import  main_src.tools.save_load_data_nopickle    as sld   # preparated

    

    
    
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
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load_data(indata)
    
    
    


    
    

    #print mat_aa
    #raw_input('')
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
    
    rainfall_file_path      = get_argv(constants.PARAMETER_PATH_TO_RAINFALL_FILE)
    if rainfall_file_path == '-' :
      pass
    # zmena deste posave, pokud se pocita jen roff
    else:
      print 'asdfdsdf'
      sr,itera  = rainfall.load_precipitation(rainfall_file_path)
    
    

    if os.path.exists(output):
      import shutil
      shutil.rmtree(output)
    if not os.path.exists(output):
      os.makedirs(output)
      #os.makedirs(output+os.sep+'prubeh')
 
    return boundaryRows, boundaryCols, \
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
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc