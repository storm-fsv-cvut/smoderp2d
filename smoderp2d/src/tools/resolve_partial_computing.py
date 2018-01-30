import os
import sys



import smoderp2d.src.constants                         as constants
from   smoderp2d.src.tools.tools                   import get_argv
from   smoderp2d.src.tools.tools                   import set_argv
from   smoderp2d.src.tools.tools                   import prt_sys_argv
from   smoderp2d.src.tools.tools                   import int_comp_type
from    smoderp2d.src.tools.tools                  import logical_argv


# # # # # # # # # # # # # # # # # # # # # # #
#from inspect import currentframe, getframeinfo
#frameinfo = getframeinfo(currentframe())
# # # # # # # # # # # # # # # # # # # # # # #



def get_indata (tc,args):


  # full computation
  #      data_preparation + runoff model
  if tc == 'full':
    from smoderp2d.src.data_preparation import prepare_data


    return  prepare_data(sys.argv)





  # only data_preparation
  #      data are saved in dump, can be stored and loaded later on
  elif tc == 'dpre':




    from smoderp2d.src.data_preparation import prepare_data
    import  smoderp2d.src.tools.save_load_data    as sld


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




    #import  smoderp2d.src.tools.save_load_data_nopickle    as sld   # preparate

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



    outoutdat = get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY) + os.sep + get_argv(constants.PARAMETER_INDATA)
    sld.save_data(dataList,outoutdat)
    #sld.save(dataList,get_argv(constants.PARAMETER_INDATA))    #   preparated


    print "Data praparation finished\n\t Data saved in ", outoutdat
    return False


    """ puvocne ty bylo sys.exit coz ale neni dobre pokud bezi skript v nadrazenem programu
    sys.exit pak muze shodit i ten. Taze se tu vrati False az do mainu a tam se nespusti
    runoff protoze tu chci jen data praparation"""




  # only runoff model
  #       data can be restored from previously prepared *.save file
  #
  elif tc == 'roff':


    # to je to je jen provizorne, pokud to bude petr delat tak jo doposud
    if len(sys.argv) > 10 :
      logical_argv(constants.PARAMETER_ARCGIS)
      logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
      logical_argv(constants.PARAMETER_MFDA)
      indata = get_argv(constants.PARAMETER_INDATA)


    else:

      import ConfigParser
      Config = ConfigParser.ConfigParser()
      Config.read(args.indata)
      sys.argv = [sys.argv.pop(0)]
      sys.argv.append(Config.get('GIS','dem'))
      sys.argv.append(Config.get('GIS','soil'))
      sys.argv.append(Config.get('shape atr','soil-atr'))
      sys.argv.append(Config.get('GIS','lu'))
      sys.argv.append(Config.get('shape atr','lu-atr'))
      sys.argv.append(Config.get('srazka','file'))
      sys.argv.append(Config.get('time','maxdt'))
      sys.argv.append(Config.get('time','endtime'))
      #sys.argv.append(Config.get('Other','reten'))
      sys.argv.append(Config.get('Other','points'))
      sys.argv.append(Config.get('Other','outdir'))
      sys.argv.append(Config.get('Other','soilvegtab'))
      sys.argv.append(Config.get('Other','soilvegcode'))
      sys.argv.append(Config.get('Other','streamshp'))
      sys.argv.append(Config.get('Other','streamtab'))
      sys.argv.append(Config.get('Other','streamtabcode'))
      sys.argv.append(Config.get('Other','arcgis'))


      sys.argv.append(Config.get('Other','mfda'))
      sys.argv.append(Config.get('Other','extraout'))
      sys.argv.append(Config.get('Other','indata'))
      sys.argv.append(Config.get('Other','partialcomp'))
      sys.argv.append(Config.get('Other','debugprt'))
      sys.argv.append(Config.get('Other','printtimes'))
      sys.argv.append(Config.get('Other','typecomp'))


      logical_argv(constants.PARAMETER_ARCGIS)
      logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
      logical_argv(constants.PARAMETER_MFDA)
      indata = get_argv(constants.PARAMETER_INDATA)



    import smoderp2d.src.tools.save_load_data  as sld
    import smoderp2d.src.processes.rainfall    as rainfall
    #import  smoderp2d.src.tools.save_load_data_nopickle    as sld   # preparated





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
    toky, cell_stream, mat_tok_usek, STREAM_RATIO, tokyLoc = sld.load(indata)   # pripraveno na pak
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