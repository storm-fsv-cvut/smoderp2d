## @package main_src.post_proc Contain a function for the post-processing
#
#  the functions are defined according to the  main_src.constants.PARAMETER_ARCGIS \n 
#  if main_src.constants.PARAMETER_ARCGIS == True: arcgis rasters are created \n
#  \n
#  if main_src.constants.PARAMETER_ARCGIS == False: ascii rasters are created \n
#  



import numpy as np
import os
import sys



import main_src.tools.tools  as tools
import main_src.constants    as constants
from   main_src.tools.tools  import get_argv
from   main_src.tools.tools                   import comp_type

## if true extra outputs are printed 
extraOutput = get_argv(constants.PARAMETER_EXTRA_OUTPUT)
## if true arcgis rasters are printed, else a ascii format is used
arcgis      = get_argv(constants.PARAMETER_ARCGIS)
## the path to the output directory
output      = get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY)



isRill, subflow, stream, diffuse = comp_type()
  
  
   
if arcgis == True :
  import arcpy
  ## creates the raster in argis format in the output directory
  def arcgis_raster(cumulative, mat_slope, G, surArr):
    
    output = G.outdir
    arcpy.env.workspace = output
    rrows = G.rr
    rcols = G.rc
    rows = G.r
    cols = G.c
    
    for i in rrows:
      for j in rcols[i]:
        cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
        cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *  mat_slope[i][j]
  
  
    main_output = [3,4,5,6,7,12,13]  #jj vyznam najdes v class Cumulative mezi class Cumulative a def__init__
    if isRill : 
      main_output += [8,9,10,11]
    if subflow :
      main_output += [14,15,16,17,18]
    if extraOutput == True :    #jj tady jen pokud chceme se i ten zbytek extraOutput je zatim definovan  na zacatku class_main_arrays
      main_output += [1,2]
    
    ll_corner = arcpy.Point(G.xllcorner, G.yllcorner)
    
    for i in main_output:
      tmparr = np.copy(getattr(cumulative, cumulative.arrs[i]))
      tmparr.fill(G.NoDataValue)
      tmpdat = np.copy(getattr(cumulative, cumulative.arrs[i]))
      for ii in rrows:
        for jj in rcols[ii]:
          tmparr[ii][jj] = tmpdat[ii][jj]
      outName = output+os.sep+cumulative.names[i]
      saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
      saveAG.save(cumulative.names[i])

    
    
    vRest     = np.zeros(np.shape(surArr),float)
    finState  = np.zeros(np.shape(surArr),int)
    hCrit     = np.zeros(np.shape(surArr),float)    
    
    #                  (   IN                                  ) - (  OUT          )  - ( What rests in the end)
    totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.V_sur) - (vRest) - cumulative.sur_ret
    
    
    outName = 'VRestEndL'
    tmparr = np.copy(vRest)
    tmparr.fill(G.NoDataValue)
    for ii in rrows:
      for jj in rcols[ii]:
        tmparr[ii][jj] = vRest[ii][jj]
    saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    saveAG.save(outName)
    
    

      
    
    outName = 'TotalBil'
    tmparr = np.copy(totalBil)
    tmparr.fill(G.NoDataValue)
    for ii in rrows:
      for jj in rcols[ii]:
        if (totalBil[ii][jj]>=1000):
          tmparr[ii][jj] = G.NoDataValue
        else:
          tmparr[ii][jj] = totalBil[ii][jj]
    saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    saveAG.save(outName)



    outName = 'FinalState'
    tmparr = np.copy(finState)
    tmparr.fill(G.NoDataValue)
    for ii in rrows:
      for jj in rcols[ii]:
        tmparr[ii][jj] = finState[ii][jj]
    saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    saveAG.save(outName)
    
    
    outName = 'HCrit'
    tmparr = np.copy(hCrit)
    tmparr.fill(G.NoDataValue)
    for ii in rrows:
      for jj in rcols[ii]:
        tmparr[ii][jj] = hCrit[ii][jj]
    saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    saveAG.save(outName)

  ## assign the ourput raster function based on the arcgis selector 
  raster_output = arcgis_raster
  
  
else:
  
  ## creates the raster in ascii format in the output directory
  def ascii_raster(cumulative, mat_slope, G, surArr):
    
    rrows = G.rr
    rcols = G.rc
    output = G.outdir
    
    for i in rrows:
      for j in rcols[i]:
        cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
        cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *  mat_slope[i][j]
  
    
    main_output = [3,4,5,6,7,12,13,14]  #jj vyznam najdes v class Cumulative mezi class Cumulative a def__init__
    if isRill : 
      main_output += [8,9,10,11]
    if subflow :
      main_output += [14,15,16,17,18]
    if extraOutput == True :    #jj tady jen pokud chceme se i ten zbytek extraOutput je zatim definovan  na zacatku class_main_arrays
      main_output += [1,2]
      
    
    finState  = np.zeros(np.shape(surArr),int)
    hCrit     = np.zeros(np.shape(surArr),float)
    Stream    = np.zeros(np.shape(surArr),float)
    Stream.fill(G.NoDataValue)
    
    
    for i in rrows:
      for j in rcols[i]:
        #vRest[i][j] =    surArr[i][j].V_rest
        finState[i][j] = int(surArr[i][j].state)
        hCrit[i][j] =    surArr[i][j].h_crit
    
    
    
    for i in main_output:
      outName = output+os.sep+cumulative.names[i]+".asc" # KAvka - zm?nit na nazvy prom?nn?ch #jj pridal jsem jmena promennych do te tridy aspon muze byt vice lidsky ten nazev ....
      wrk = getattr(cumulative, cumulative.arrs[i])
      for i in rrows:
        for j in rcols[i]:
          if (finState[i][j] >= 1000) :
            wrk[i][j] = G.NoDataValue
      tools.make_ASC_raster(outName,wrk,G)
    
    
    #outName = output+os.sep+'VRestEndL'+".asc" 
    #tools.make_ASC_raster(outName,vRest,G)
    
    totalBil = cumulative.infiltration.copy()
    totalBil.fill(0.0)
    
    #          (   IN                                           ) - (  OUT                                                         )  - ( What rests in the end)
    totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.V_sur + cumulative.V_rill) - cumulative.sur_ret #+ (cumulative.V_sur_r + cumulative.V_rill_r) 
    
    vRest     = np.zeros(np.shape(surArr),float)
    if isRill : 
      for i in rrows:
        for j in rcols[i]:
          if (finState[i][j] >= 1000) :
            vRest[i][j] =    G.NoDataValue
          else :
            vRest[i][j] =  surArr[i][j].h_total_new*G.pixel_area
          
          
      outName = output+os.sep+'VRestEndRillL3'+".asc" 
      tools.make_ASC_raster(outName,vRest,G)
      totalBil +=   -vRest
      
    for i in rrows:
      for j in rcols[i]:
        if (finState[i][j] >= 1000) :
          totalBil[i][j] = G.NoDataValue
          Stream[i][j]   = finState[i][j]
          hCrit[i][j]    = G.NoDataValue
      
      
    outName = output+os.sep+'Stream'+".asc" 
    tools.make_ASC_raster(outName,Stream,G)
    
    
    outName = output+os.sep+'TotalBil'+".asc" 
    tools.make_ASC_raster(outName,totalBil,G)
    
    
    
    outName = output+os.sep+'FinalState'+".asc" 
    tools.make_ASC_raster(outName,finState,G)
    
    
    
    outName = output+os.sep+'HCrit'+".asc" 
    tools.make_ASC_raster(outName,hCrit,G)
    
    
    
      
    
    
    
    
    
  ## assign the ourput raster function based on the arcgis selector 
  raster_output = ascii_raster

    





if stream and arcgis:
  import arcpy
  def write_stream_table(outDir, surface,toky):
    sep = ';'
    nReaches = surface.nReaches
    outFile = outDir + 'stream.txt'
    outFileShp = outDir + 'stream.shp'
    outTemp  = outDir #+ 'temp' + os.sep
    with open(outFile, 'w') as f:
      line = 'FID'+sep+'V_out_cum [L^3]'+sep+'Q_max [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max [L]'+sep+'timeh_max[s]'+sep+'Cumulatice_inflow_from_field[L^3]' + sep+ 'Left_after_last_time_step[L^3]'   + sep+ 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
      f.write(line)
      for iReach in range(nReaches):
        line = \
          str(surface.reach[iReach].id_) +sep+  \
            str(surface.reach[iReach].V_out_cum) +sep+   \
              str(surface.reach[iReach].Q_max) +sep+ str(surface.reach[iReach].timeQ_max)  +sep+ str(surface.reach[iReach].h_max) +sep+str(surface.reach[iReach].timeh_max) +sep+\
                str(surface.reach[iReach].V_in_from_field_cum) +sep+ str(surface.reach[iReach].V_rest) +sep+ \
                str(surface.reach[iReach].V_out_domain) +sep+ str(surface.reach[iReach].to_node)\
                + '\n'
        f.write(line)
  
    arcpy.MakeFeatureLayer_management(toky,outTemp+"streamtmp.shp")
    arcpy.AddJoin_management(outTemp+"streamtmp.shp","FID",outFile,"FID")
    arcpy.CopyFeatures_management(outTemp+"streamtmp.shp",outFileShp)

  
  stream_table = write_stream_table
  


  


elif stream and not(arcgis):
  def write_stream_table(outDir, surface,toky):
    sep = ';'
    nReaches = surface.nReaches
    outFile = outDir + 'stream.txt'
    with open(outFile, 'w') as f:
      line = '# FID'+sep+'V_out_cum [L^3]'+sep+'Q_max [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max [L]'+sep+'timeh_max[s]'+sep+'Cumulatice_inflow_from_field[L^3]' + sep+ 'Left_after_last_time_step[L^3]'   + sep+ 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
      f.write(line)
      for iReach in range(nReaches):
        line = \
          str(surface.reach[iReach].id_) +sep+  \
            str(surface.reach[iReach].V_out_cum) +sep+   \
              str(surface.reach[iReach].Q_max) +sep+ str(surface.reach[iReach].timeQ_max)  +sep+ str(surface.reach[iReach].h_max) +sep+str(surface.reach[iReach].timeh_max) +sep+\
                str(surface.reach[iReach].V_in_from_field_cum) +sep+ str(surface.reach[iReach].V_rest) +sep+ \
                str(surface.reach[iReach].V_out_domain) +sep+ str(surface.reach[iReach].to_node)\
                + '\n'
        f.write(line)
        
  stream_table = write_stream_table
  
else:
  
  def pass_stream_table(outDir, surface,toky):
    pass
  
  stream_table = pass_stream_table

