# @package smoderp2d.post_proc Contain a function for the post-processing

import numpy as np
import os
import shutil

from smoderp2d.core.general import Globals
from smoderp2d.core.general import GridGlobals


def do(cumulative, mat_slope, G, surArr):
    output = Globals.outdir
    rrows = GridGlobals.rr
    rcols = GridGlobals.rc

    for i in rrows:
        for j in rcols[i]:
            if cumulative.h_sur[i][j] == 0.:
                cumulative.v_sheet[i][j] = 0.
            else:
                cumulative.v_sheet[i][j] = cumulative.q_sheet[
                                               i][j] / cumulative.h_sur[i][j]
            cumulative.shear_sheet[i][j] = cumulative.h_sur[
                                               i][j] * 98.07 * mat_slope[i][j]

    main_output = ['infiltration',
                   'precipitation',
                   'v_sur2',
                   'shear_sur',
                   'q_sur_tot',
                   'v_sur_tot']

    if Globals.subflow:
        main_output += ['v_sur_r',
                        'q_sur_tot',
                        'v_sur_tot',
                        'exfiltration',
                        'percolation']
    if Globals.extraOut:
        # jj tady jen pokud chceme se i ten zbytek Globals.extraOut je zatim
        # definovan na zacatku class_main_arrays
        main_output += ['q_sur',
                        'h_rill',
                        'q_rill',
                        'b_rill',
                        'inflow_sur',
                        'sur_ret',
                        'v_sur_r']

    finState = np.zeros(np.shape(surArr), int)
    finState.fill(GridGlobals.NoDataValue)
    vRest = np.zeros(np.shape(surArr), float)
    vRest.fill(GridGlobals.NoDataValue)
    totalBil = cumulative.infiltration.copy()
    totalBil.fill(0.0)

    for i in rrows:
        for j in rcols[i]:
            finState[i][j] = int(surArr[i][j].state)

    # make rasters from cumulative class
    for i in main_output:
        # arrin = np.copy(getattr(cumulative, cumulative.arrs[i]))
        # outname = cumulative.arrs[i]
        raster_output(i, G, finState, cumulative.arrs[i][1])

    for i in rrows:
        for j in rcols[i]:
            if finState[i][j] >= 1000:
                vRest[i][j] = GridGlobals.NoDataValue
            else:
                vRest[i][j] = surArr[i][j].h_total_new * GridGlobals.pixel_area

    totalBil = (cumulative.precipitation + cumulative.inflow_sur) - \
               (cumulative.infiltration + cumulative.v_sur +
                cumulative.v_rill) - cumulative.sur_ret
    # + (cumulative.v_sur_r + cumulative.v_rill_r)
    totalBil -= vRest

    # raster_output(totalBil, G, finState, 'massBalance')
    # raster_output(finState, G, finState, 'reachfid', False)
    # raster_output(vRest, G, finState, 'volrest_m3')

    if not Globals.extraOut:
        if os.path.exists(output + os.sep + 'temp'):
            shutil.rmtree(output + os.sep + 'temp')
        if os.path.exists(output + os.sep + 'temp_dp'):
            shutil.rmtree(output + os.sep + 'temp_dp')
        return 1


################################
# creates the raster in argis format in the output directory
# def Globals.arcgis_raster(cumulative, mat_slope, G, surArr):

# output = Globals.outdir
# arcpy.env.workspace = output
# rrows = GridGlobals.rr
# rcols = GridGlobals.rc
# rows = GridGlobals.r
# cols = GridGlobals.c

# for i in rrows:
# for j in rcols[i]:
# cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
# cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *
# mat_slope[i][j]

# main_output = [1,2,3,5,6,7,10,15]  #jj vyznam najdes v class
# Cumulative mezi class Cumulative a def__init__

# if Globals.subflow :
# main_output += [14,15,16,17,18]
# if Globals.extraOut == True :
    # # jj tady jen pokud chceme se i ten zbytek Globals.extraOut je zatim
    # # definovan  na zacatku class_main_arrays
# main_output += [4,8,9,11,12,13,14]

# ll_corner = arcpy.Point(GridGlobals.xllcorner, GridGlobals.yllcorner)

# for i in main_output:
# arrin = np.copy(getattr(cumulative, cumulative.arrs[i]))
# raster_output_Globals.arcgis (aarin, G)

# vRest     = np.zeros(np.shape(surArr),float)
# finState  = np.zeros(np.shape(surArr),int)
# hCrit     = np.zeros(np.shape(surArr),float)
# finState.fill(GridGlobals.NoDataValue)

# vRest     = np.zeros(np.shape(surArr),float)
# if Globals.isRill :
# for i in rrows:
# for j in rcols[i]:
# if (finState[i][j] >= 1000) :
# vRest[i][j] =    GridGlobals.NoDataValue
# else :
# vRest[i][j] =  surArr[i][j].h_total_new*GridGlobals.pixel_area

# (   IN                                           ) - (  OUT                                                         )  - ( What rests in the end)
# totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration + cumulative.v_sur + cumulative.v_rill) - cumulative.sur_ret #+ (cumulative.v_sur_r + cumulative.v_rill_r)
# totalBil -= vRest

# for i in rrows:
# for j in rcols[i]:
# vRest[i][j] =    surArr[i][j].vol_rest
# finState[i][j] = int(surArr[i][j].state)

# outName = 'reachFID'
# tmparr = np.copy(finState)
# saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, GridGlobals.dx, GridGlobals.dy, GridGlobals.NoDataValue)
# saveAG.save(outName)

# outName = 'massBalance'
# tmparr = np.copy(totalBil)
# tmparr.fill(GridGlobals.NoDataValue)
# for ii in rrows:
# for jj in rcols[ii]:
# if (finState[ii][jj]>=1000):
# tmparr[ii, jj] = GridGlobals.NoDataValue
# else:
# tmparr[ii, jj] = totalBil[ii][jj]
# saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, GridGlobals.dx, GridGlobals.dy, GridGlobals.NoDataValue)
# saveAG.save(outName)

# tmparr.fill(GridGlobals.NoDataValue)
# for ii in rrows:
# for jj in rcols[ii]:
# if (totalBil[ii][jj]>=2000):
# tmparr[ii, jj] = GridGlobals.mat_stream_seg
# if (totalBil[ii][jj]>=1):
# tmparr[ii, jj] = 1
# else:
# tmparr[ii, jj] = totalBil[ii][jj]

# pokud nechci extra output opoustim funkci tu
# if not(Globals.extraOut) :
# return 1

# outName = 'VRestEndL'
# tmparr = np.copy(vRest)
# tmparr.fill(GridGlobals.NoDataValue)
# for ii in rrows:
# for jj in rcols[ii]:
# tmparr[ii, jj] = vRest[ii][jj]
# saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, GridGlobals.dx, GridGlobals.dy, GridGlobals.NoDataValue)
# saveAG.save(outName)

# outName = 'FinalState'
# tmparr = np.copy(finState)
# tmparr.fill(GridGlobals.NoDataValue)
# for ii in rrows:
# for jj in rcols[ii]:
# tmparr[ii, jj] = finState[ii][jj]
# saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, GridGlobals.dx, GridGlobals.dy, GridGlobals.NoDataValue)
# saveAG.save(outName)

# outName = 'HCrit'
# tmparr = np.copy(hCrit)
# tmparr.fill(GridGlobals.NoDataValue)
# for ii in rrows:
# for jj in rcols[ii]:
# tmparr[ii, jj] = hCrit[ii][jj]
# saveAG = arcpy.NumPyArrayToRaster(tmparr, ll_corner, GridGlobals.dx, GridGlobals.dy, GridGlobals.NoDataValue)
# saveAG.save(outName)

# assign the ourput raster function based on the Globals.arcgis selector
# raster_output = Globals.arcgis_raster


# else:

# creates the raster in ascii format in the output directory
# def ascii_raster(cumulative, mat_slope, G, surArr):
# rrows = GridGlobals.rr
# rcols = GridGlobals.rc
# output = GridGlobals.outdir

# for i in rrows:
# for j in rcols[i]:
# cumulative.v_sur[i][j] = cumulative.q_sur[i][j]/cumulative.h_sur[i][j]
# cumulative.shear_sur[i][j] = cumulative.h_sur[i][j] * 98.07 *
# mat_slope[i][j]

# main_output = [1,2,3,5,6,7,10,15]  #jj vyznam najdes v class
# Cumulative mezi class Cumulative a def__init__

# if Globals.subflow :
# main_output += [14,15,16,17,18]
# if Globals.extraOut == True :    #jj tady jen pokud chceme se i ten zbytek Globals.extraOut je zatim definovan  na zacatku class_main_arrays
# main_output += [4,8,9,11,12,13,14]

# finState  = np.zeros(np.shape(surArr),int)
# hCrit     = np.zeros(np.shape(surArr),float)
# Stream    = np.zeros(np.shape(surArr),float)
# Stream.fill(GridGlobals.NoDataValue)

# for i in rrows:
# for j in rcols[i]:
# vRest[i][j] =    surArr[i][j].vol_rest
# finState[i][j] = int(surArr[i][j].state)
# hCrit[i][j] =    surArr[i][j].h_crit

# for i in main_output:

# outName = output+os.sep+'VRestEndL'+".asc"
# tools.make_ASC_raster(outName,vRest,G)

# totalBil = cumulative.infiltration.copy()
# totalBil.fill(0.0)

# (   IN                                           ) - (  OUT                                                         )  - ( What rests in the end)
# totalBil = (cumulative.precipitation + cumulative.inflow_sur) -
# (cumulative.infiltration + cumulative.v_sur + cumulative.v_rill) -
# cumulative.sur_ret #+ (cumulative.v_sur_r + cumulative.v_rill_r)

# vRest     = np.zeros(np.shape(surArr),float)
# if Globals.isRill :
# for i in rrows:
# for j in rcols[i]:
# if (finState[i][j] >= 1000) :
# vRest[i][j] =    GridGlobals.NoDataValue
# else :
# vRest[i][j] =  surArr[i][j].h_total_new*GridGlobals.pixel_area

# outName = output+os.sep+'VRestEndRillL3'+".asc"
# tools.make_ASC_raster(outName,vRest,G)
# totalBil +=   -vRest

# for i in rrows:
# for j in rcols[i]:
# if (finState[i][j] >= 1000) :
# totalBil[i][j] = GridGlobals.NoDataValue
# Stream[i][j]   = finState[i][j]
# hCrit[i][j]    = GridGlobals.NoDataValue

# outName = output+os.sep+'massBalance'+".asc"
# tools.make_ASC_raster(outName,totalBil,G)

# outName = output+os.sep+'reachFID'+".asc"
# tools.make_ASC_raster(outName,finState,G)

# pokud nechci extra output opoustim funkci tu
# if not(Globals.extraOut) :
# return 1

# outName = output+os.sep+'Stream'+".asc"
# tools.make_ASC_raster(outName,Stream,G)

# outName = output+os.sep+'FinalState'+".asc"
# tools.make_ASC_raster(outName,finState,G)

# outName = output+os.sep+'HCrit'+".asc"
# tools.make_ASC_raster(outName,hCrit,G)

# assign the ourput raster function based on the Globals.arcgis selector
# raster_output = ascii_raster


# TODO
# if Globals.isStream and Globals.arcgis:
#     import arcpy

#     def write_stream_table(outDir, surface, streams):
#         sep = ';'
#         nReaches = surface.nReaches
#         outFile = outDir + 'hydReach.txt'
#         outFileShp = outDir + 'hydReach.shp'
#         outTemp = outDir  # + 'temp' + os.sep
#         with open(outFile, 'w') as f:
#             line = 'FID' + sep + 'cVolM3' + sep + 'mFlowM3_S' + sep + 'mFlowTimeS' + \
#                 sep + 'mWatLM' + sep + 'restVolM3' + sep + 'toFID' + '\n'
#             # line = 'FID'+sep+'v_out_cum [L^3]'+sep+'Q_max
#             # [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max
#             # [L]'+sep+'timeh_max[s]'+sep+'Cumulatice_inflow_from_field[L^3]' +
#             # sep+ 'Left_after_last_time_step[L^3]'   + sep+
#             # 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
#             f.write(line)
#             for iReach in range(nReaches):
#                 line = \
#                     str(surface.reach[iReach].id_) + sep +  \
#                     str(surface.reach[iReach].v_out_cum) + sep +   \
#                       str(surface.reach[iReach].Q_max) + sep + str(surface.reach[iReach].timeQ_max)  + sep + str(surface.reach[iReach].h_max) + sep + \
#                         str(surface.reach[iReach].vol_rest) + sep + \
#                           str(surface.reach[iReach].to_node) + '\n'

#                 f.write(line)

#         arcpy.MakeFeatureLayer_management(streams, outTemp + "Globals.streamtmp.shp")
#         arcpy.AddJoin_management(
#             outTemp +
#             "Globals.streamtmp.shp",
#             "FID",
#             outFile,
#             "FID")
#         arcpy.CopyFeatures_management(outTemp + "Globals.streamtmp.shp", outFileShp)

#     stream_table = write_stream_table


# elif Globals.isStream and not(Globals.arcgis):
#     def write_stream_table(outDir, surface, streams):
#         sep = ';'
#         nReaches = surface.nReaches
#         outFile = outDir + 'hydReach.txt'
#         with open(outFile, 'w') as f:
#             line = 'FID' + sep + 'cVolM3' + sep + 'mFlowM3_S' + sep + 'mFlowTimeS' + \
#                 sep + 'mWatLM' + sep + 'restVolM3' + sep + 'toFID' + '\n'
#             # line = 'FID'+sep+'v_out_cum [L^3]'+sep+'Q_max
#             # [L^3.t^{-1}]'+sep+'timeQ_max[s]'+sep+'h_max
#             # [L]'+sep+'timeh_max[s]'+sep+'Cumulative_inflow_from_field[L^3]' +
#             # sep+ 'Left_after_last_time_step[L^3]'   + sep+
#             # 'Out_form_domain[L^3]'+sep+'to_reach'+'\n'
#             f.write(line)
#             for iReach in range(nReaches):
#                 line = \
#                     str(surface.reach[iReach].id_) + sep +  \
#                     str(surface.reach[iReach].V_out_cum) + sep +   \
#                       str(surface.reach[iReach].Q_max) + sep + str(surface.reach[iReach].timeQ_max)  + sep + str(surface.reach[iReach].h_max) + sep + \
#                         str(surface.reach[iReach].vol_rest) + sep + \
#                         str(surface.reach[iReach].to_node) + '\n'

#                 f.write(line)

#     stream_table = write_stream_table

# else:

def pass_stream_table(outDir, surface, streams):
    pass


stream_table = pass_stream_table
