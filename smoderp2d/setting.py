


def get_indata ():
  import config
  
  
  pc     = config.get_partialComp()
  indata = config.get_inData()
  print pc
  
  # full computation
  #      data_preparation + runoff model
  if pc == 'full':
    from smoderp2d.src.data_preparation import prepare_data


    return  prepare_data(sys.argv)

    



  # only data_preparation
  #      data are saved in dump, can be stored and loaded later on
  elif pc == 'dpre':

    


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
    
    
    sld.save_data(dataList,get_argv(constants.PARAMETER_INDATA))
    #sld.save(dataList,get_argv(constants.PARAMETER_INDATA))    #   preparated

          
    print "Data praparation finished\n\t Data saved in ", get_argv(constants.PARAMETER_INDATA)
    return False
    
    
    """ puvocne ty bylo sys.exit coz ale neni dobre pokud bezi skript v nadrazenem programu
    sys.exit pak muze shodit i ten. Taze se tu vrati False az do mainu a tam se nespusti
    runoff protoze tu chci jen data praparation"""




  # only runoff model
  #       data can be restored from previously prepared *.save file
  #       
  elif pc == 'roff':
    
    # tento if jen kvuli testovani
    # pri tom jsem poustel primo setting
    if __name__ == "__main__" :
      import src.tools.save_load_data  as sld
      #import src.processes.rainfall    as rainfall
    else :
      import smoderp2d.src.tools.save_load_data  as sld
      import smoderp2d.src.processes.rainfall    as rainfall #toto bude fungocat az bute setup spojen se semoderpem
      
    #import  smoderp2d.src.tools.save_load_data_nopickle    as sld   # pripraveno na jindy

    

    
    
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


    if config.get_outDirPath() == '-':
      config.set_outDirPath(output)
      
    if config.get_endTime() == '-':
      config.set_endTime(end_time*60)  
      
    if config.get_mfda() == '-':
      config.set_mfda(mfda)  
    
    if config.get_type() == '-':
      config.set_mfda(mfda)  
      
      
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
      if __name__ == '__main__' :
        sr = 0
        itera = 0
      else :
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











def init_win() :
  pass  
  
  
  
  
  
  

def init_lin() :
  
  import argparse
  
  
  # tento if jen kvuli testovani
  # pri tom jsem poustel primo setting
  if __name__ == "__main__" :
    import config
    import glob
  else :  
    import smoderp2d.config
    import smoderp2d.glob
  
  
  
  parser = argparse.ArgumentParser()
  parser.add_argument('typecomp', help='type of computation', type=str, choices=['full','dpre','roff'])
  parser.add_argument('--indata', help='file with input data', type=str)
  args = parser.parse_args()
  
  
  # assign input paramters into config data
  config.set_config_lin(args)
  
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
  
  
  
  
  
  
  
if __name__ == "__main__":
  init_lin()
  
  