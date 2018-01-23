## @package smoderp2d.src.post_proc Contain a function for the post-processing
#
#  the functions are defined according to the  smoderp2d.src.constants.PARAMETER_ARCGIS \n
#  if smoderp2d.src.constants.PARAMETER_ARCGIS == True: arcgis rasters are created \n
#  \n
#  if smoderp2d.src.constants.PARAMETER_ARCGIS == False: ascii rasters are created \n
#



import numpy as np
import os
import sys
import shutil



import smoderp2d.src.tools.tools  as tools
import smoderp2d.src.constants    as constants
from   smoderp2d.src.tools.tools  import get_argv
from   smoderp2d.src.tools.tools                   import comp_type
import smoderp2d.src.io_functions.prt as prt
from    smoderp2d.src.tools.tools                  import logical_argv


## if true extra outputs are printed
logical_argv(constants.PARAMETER_EXTRA_OUTPUT)
extraOutput = get_argv(constants.PARAMETER_EXTRA_OUTPUT)
## if true arcgis rasters are printed, else a ascii format is used
logical_argv(constants.PARAMETER_ARCGIS)
arcgis      = get_argv(constants.PARAMETER_ARCGIS)
## the path to the output directory




isRill, subflow, stream, diffuse = comp_type()



def raster_output_arcgis (arrin, G, fs, outname, reachNA=True) :
    import arcpy
    rrows = G.rr
    rcols = G.rc
    output = G.outdir
    arcpy.env.workspace = output
    ll_corner = arcpy.Point(G.xllcorner, G.yllcorner)
    tmparr = arrin.copy()
    tmparr.fill(G.NoDataValue)
    tmpdat = arrin.copy()
    for ii in rrows:
      for jj in rcols[ii]:
        # prt.message(tmpdat[ii][jj])
        tmparr[ii][jj] = tmpdat[ii][jj]
    outName = output+os.sep+outname
    saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    saveAG.save(outName)




def raster_output_ascii (arrin, G, fs, outname, reachNA=True) :
    output = G.outdir
    outName = output+os.sep+outname+".asc" # KAvka - zm?nit na nazvy prom?nn?ch #jj pridal jsem jmena promennych do te tridy aspon muze byt vice lidsky ten nazev ....
    wrk = arrin
    rrows = G.rr
    rcols = G.rc
    if (reachNA) :
      for i in rrows:
        for j in rcols[i]:
          if (fs[i][j] >= 1000) :
            wrk[i][j] = G.NoDataValue
    tools.make_ASC_raster(outName,wrk,G)




if arcgis == True :
  raster_output = raster_output_arcgis
else :
  raster_output = raster_output_ascii



def do (cumulative, mat_slope, G, surArr) :

  output = G.outdir
  rrows = G.rr
  rcols = G.rc


  for i in rrows:
    for j in rcols[i]:
      if cumulative.h_sur[i][j] == 0.:
        cumulative.v_sur[i][j] = 0.
      else :
        cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
      cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *  mat_slope[i][j]

  #1, 2, 15, 16
  main_output = [1, 2, 6, 7, 15, 16]  #jj vyznam najdes v class Cumulative mezi class Cumulative a def__init__

  if subflow :
    main_output += [14,15,16,17,18]
  if extraOutput == True :    #jj tady jen pokud chceme se i ten zbytek extraOutput je zatim definovan  na zacatku class_main_arrays
    main_output += [4,8,9,11,12,13,14]

  finState  = np.zeros(np.shape(surArr),int)
  finState.fill(G.NoDataValue)
  vRest     = np.zeros(np.shape(surArr),float)
  vRest.fill(G.NoDataValue)
  totalBil = cumulative.infiltration.copy()
  totalBil.fill(0.0)

  for i in rrows:
    for j in rcols[i]:
       finState[i][j] = int(surArr[i][j].state)


  # make rasters from cumulative class
  for i in main_output:
    arrin = np.copy(getattr(cumulative, cumulative.arrs[i]))
    outname = cumulative.names[i]
    raster_output(arrin, G, finState, outname)


  for i in rrows:
    for j in rcols[i]:
      if (finState[i][j] >= 1000) :
        vRest[i][j] =    G.NoDataValue
      else :
        vRest[i][j] =  surArr[i][j].h_total_new*G.pixel_area


  totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.V_sur + cumulative.V_rill) - cumulative.sur_ret #+ (cumulative.V_sur_r + cumulative.V_rill_r)
  totalBil -= vRest


  raster_output(totalBil, G, finState, 'massBalance')
  raster_output(finState, G, finState, 'reachfid',False)
  raster_output(vRest, G, finState, 'volrest_m3')







  if not(extraOutput) :
    if os.path.exists(output + os.sep + 'temp'):
      shutil.rmtree(output + os.sep + 'temp')
    if os.path.exists(output + os.sep + 'temp_dp'):
      shutil.rmtree(output + os.sep + 'temp_dp')
    return 1


  ####### creates the raster in argis format in the output directory
  #####def arcgis_raster(cumulative, mat_slope, G, surArr):

    #####output = G.outdir
    #####arcpy.env.workspace = output
    #####rrows = G.rr
    #####rcols = G.rc
    #####rows = G.r
    #####cols = G.c

    #####for i in rrows:
      #####for j in rcols[i]:
        #####cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
        #####cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *  mat_slope[i][j]


    #####main_output = [1,2,3,5,6,7,10,15]  #jj vyznam najdes v class Cumulative mezi class Cumulative a def__init__

    #####if subflow :
      #####main_output += [14,15,16,17,18]
    #####if extraOutput == True :    #jj tady jen pokud chceme se i ten zbytek extraOutput je zatim definovan  na zacatku class_main_arrays
      #####main_output += [4,8,9,11,12,13,14]

    #####ll_corner = arcpy.Point(G.xllcorner, G.yllcorner)



    #####for i in main_output:
      #####arrin = np.copy(getattr(cumulative, cumulative.arrs[i]))
      #####raster_output_arcgis (aarin, G)



    #####vRest     = np.zeros(np.shape(surArr),float)
    #####finState  = np.zeros(np.shape(surArr),int)
    #####hCrit     = np.zeros(np.shape(surArr),float)
    #####finState.fill(G.NoDataValue)


    #####vRest     = np.zeros(np.shape(surArr),float)
    #####if isRill :
      #####for i in rrows:
        #####for j in rcols[i]:
          #####if (finState[i][j] >= 1000) :
            #####vRest[i][j] =    G.NoDataValue
          #####else :
            #####vRest[i][j] =  surArr[i][j].h_total_new*G.pixel_area

    ######          (   IN                                           ) - (  OUT                                                         )  - ( What rests in the end)
    #####totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.V_sur + cumulative.V_rill) - cumulative.sur_ret #+ (cumulative.V_sur_r + cumulative.V_rill_r)
    #####totalBil -= vRest





    #####for i in rrows:
      #####for j in rcols[i]:
        ######vRest[i][j] =    surArr[i][j].V_rest
        #####finState[i][j] = int(surArr[i][j].state)






    #####outName = 'reachFID'
    #####tmparr = np.copy(finState)
    #####saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    #####saveAG.save(outName)




    #####outName = 'massBalance'
    #####tmparr = np.copy(totalBil)
    #####tmparr.fill(G.NoDataValue)
    #####for ii in rrows:
      #####for jj in rcols[ii]:
        #####if (finState[ii][jj]>=1000):
          #####tmparr[ii][jj] = G.NoDataValue
        #####else:
          #####tmparr[ii][jj] = totalBil[ii][jj]
    #####saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    #####saveAG.save(outName)




    ######tmparr.fill(G.NoDataValue)
    ######for ii in rrows:
      ######for jj in rcols[ii]:
        ######if (totalBil[ii][jj]>=2000):
          ######tmparr[ii][jj] = G.mat_tok_usek
        ######if (totalBil[ii][jj]>=1):
          ######tmparr[ii][jj] = 1
        ######else:
          ######tmparr[ii][jj] = totalBil[ii][jj]



    ###### pokud nechci extra output opoustim funkci tu
    #####if not(extraOutput) :
      #####return 1





    #####outName = 'VRestEndL'
    #####tmparr = np.copy(vRest)
    #####tmparr.fill(G.NoDataValue)
    #####for ii in rrows:
      #####for jj in rcols[ii]:
        #####tmparr[ii][jj] = vRest[ii][jj]
    #####saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    #####saveAG.save(outName)








    #####outName = 'FinalState'
    #####tmparr = np.copy(finState)
    #####tmparr.fill(G.NoDataValue)
    #####for ii in rrows:
      #####for jj in rcols[ii]:
        #####tmparr[ii][jj] = finState[ii][jj]
    #####saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    #####saveAG.save(outName)


    #####outName = 'HCrit'
    #####tmparr = np.copy(hCrit)
    #####tmparr.fill(G.NoDataValue)
    #####for ii in rrows:
      #####for jj in rcols[ii]:
        #####tmparr[ii][jj] = hCrit[ii][jj]
    #####saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, G.dx, G.dy, G.NoDataValue)
    #####saveAG.save(outName)

  ####### assign the ourput raster function based on the arcgis selector
  #####raster_output = arcgis_raster


#####else:

  ####### creates the raster in ascii format in the output directory
  #####def ascii_raster(cumulative, mat_slope, G, surArr):
    #####rrows = G.rr
    #####rcols = G.rc
    #####output = G.outdir

    #####for i in rrows:
      #####for j in rcols[i]:
        #####cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
        #####cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *  mat_slope[i][j]


    #####main_output = [1,2,3,5,6,7,10,15]  #jj vyznam najdes v class Cumulative mezi class Cumulative a def__init__

    #####if subflow :
      #####main_output += [14,15,16,17,18]
    #####if extraOutput == True :    #jj tady jen pokud chceme se i ten zbytek extraOutput je zatim definovan  na zacatku class_main_arrays
      #####main_output += [4,8,9,11,12,13,14]



    #####finState  = np.zeros(np.shape(surArr),int)
    #####hCrit     = np.zeros(np.shape(surArr),float)
    #####Stream    = np.zeros(np.shape(surArr),float)
    #####Stream.fill(G.NoDataValue)


    #####for i in rrows:
      #####for j in rcols[i]:
        ######vRest[i][j] =    surArr[i][j].V_rest
        #####finState[i][j] = int(surArr[i][j].state)
        #####hCrit[i][j] =    surArr[i][j].h_crit



    #####for i in main_output:






    ######outName = output+os.sep+'VRestEndL'+".asc"
    ######tools.make_ASC_raster(outName,vRest,G)

    #####totalBil = cumulative.infiltration.copy()
    #####totalBil.fill(0.0)

    ######          (   IN                                           ) - (  OUT                                                         )  - ( What rests in the end)
    #####totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.V_sur + cumulative.V_rill) - cumulative.sur_ret #+ (cumulative.V_sur_r + cumulative.V_rill_r)

    #####vRest     = np.zeros(np.shape(surArr),float)
    #####if isRill :
      #####for i in rrows:
        #####for j in rcols[i]:
          #####if (finState[i][j] >= 1000) :
            #####vRest[i][j] =    G.NoDataValue
          #####else :
            #####vRest[i][j] =  surArr[i][j].h_total_new*G.pixel_area


      #####outName = output+os.sep+'VRestEndRillL3'+".asc"
      #####tools.make_ASC_raster(outName,vRest,G)
      #####totalBil +=   -vRest

    #####for i in rrows:
      #####for j in rcols[i]:
        #####if (finState[i][j] >= 1000) :
          #####totalBil[i][j] = G.NoDataValue
          #####Stream[i][j]   = finState[i][j]
          #####hCrit[i][j]    = G.NoDataValue

    #####outName = output+os.sep+'massBalance'+".asc"
    #####tools.make_ASC_raster(outName,totalBil,G)




    #####outName = output+os.sep+'reachFID'+".asc"
    #####tools.make_ASC_raster(outName,finState,G)






    ###### pokud nechci extra output opoustim funkci tu
    #####if not(extraOutput) :
      #####return 1


    #####outName = output+os.sep+'Stream'+".asc"
    #####tools.make_ASC_raster(outName,Stream,G)





    #####outName = output+os.sep+'FinalState'+".asc"
    #####tools.make_ASC_raster(outName,finState,G)



    #####outName = output+os.sep+'HCrit'+".asc"
    #####tools.make_ASC_raster(outName,hCrit,G)









  ####### assign the ourput raster function based on the arcgis selector
  #####raster_output = ascii_raster







if stream and arcgis:
  import arcpy
  def write_stream_table(outDir, surface,toky):
    sep = ';'
    nReaches = surface.nReaches
    outFile = outDir + 'hydReach.txt'
    outFileShp = outDir + 'hydReach.shp'
    outTemp  = outDir #+ 'temp' + os.sep
    with open(outFile, 'w') as f:
      line = 'FID'+sep+'cVolM3'+sep+'mFlowM3_S'+sep+'mFlowTimeS'+sep+'mWatLM'+sep+'restVolM3' + sep + 'toFID'+'\n'
      #line = 'FID'+sep+'V_out_cum [L^3]'+sep+'Q_max [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max [L]'+sep+'timeh_max[s]'+sep+'Cumulatice_inflow_from_field[L^3]' + sep+ 'Left_after_last_time_step[L^3]'   + sep+ 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
      f.write(line)
      for iReach in range(nReaches):
        line = \
          str(surface.reach[iReach].id_) +sep+  \
            str(surface.reach[iReach].V_out_cum) +sep+   \
              str(surface.reach[iReach].Q_max) +sep+ str(surface.reach[iReach].timeQ_max)  +sep+ str(surface.reach[iReach].h_max) +sep+ \
                str(surface.reach[iReach].V_rest) +sep+ \
                  str(surface.reach[iReach].to_node) + '\n'

        f.write(line)

    arcpy.MakeFeatureLayer_management(toky,outTemp+"streamtmp.shp")
    arcpy.AddJoin_management(outTemp+"streamtmp.shp","FID",outFile,"FID")
    arcpy.CopyFeatures_management(outTemp+"streamtmp.shp",outFileShp)


  stream_table = write_stream_table






elif stream and not(arcgis):
  def write_stream_table(outDir, surface,toky):
    sep = ';'
    nReaches = surface.nReaches
    outFile = outDir + 'hydReach.txt'
    with open(outFile, 'w') as f:
      line = 'FID'+sep+'cVolM3'+sep+'mFlowM3_S'+sep+'mFlowTimeS'+sep+'mWatLM'+sep+'restVolM3' + sep + 'toFID'+'\n'
      #line = 'FID'+sep+'V_out_cum [L^3]'+sep+'Q_max [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max [L]'+sep+'timeh_max[s]'+sep+'Cumulatice_inflow_from_field[L^3]' + sep+ 'Left_after_last_time_step[L^3]'   + sep+ 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
      f.write(line)
      for iReach in range(nReaches):
        line = \
          str(surface.reach[iReach].id_) +sep+  \
            str(surface.reach[iReach].V_out_cum) +sep+   \
              str(surface.reach[iReach].Q_max) +sep+ str(surface.reach[iReach].timeQ_max)  +sep+ str(surface.reach[iReach].h_max) +sep+ \
                str(surface.reach[iReach].V_rest) +sep+ \
                  str(surface.reach[iReach].to_node) + '\n'

        f.write(line)

  stream_table = write_stream_table

else:

  def pass_stream_table(outDir, surface,toky):
    pass

  stream_table = pass_stream_table

