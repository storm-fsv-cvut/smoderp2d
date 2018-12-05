# @package smoderp2d.post_proc Contain a function for the post-processing


import numpy as np
import os
import sys
import shutil


import smoderp2d.tools.tools as tools
from smoderp2d.core.general import Globals as Gl


def raster_output_arcgis(arrin, G, fs, outname, reachNA=True):
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
            tmparr[ii][jj] = tmpdat[ii][jj]
    outName = output + os.sep + outname
    saveAG = arcpy.NumPyArrayToRaster(
        tmparr,
        ll_corner,
        G.dx,
        G.dy,
        G.NoDataValue)
    saveAG.save(outName)


def raster_output_ascii(arrin, G, fs, outname, reachNA=True):
    output = G.outdir
    outName = output + os.sep + outname + \
        ".asc"  # KAvka - zm?nit na nazvy prom?nn?ch #jj pridal jsem jmena promennych do te tridy aspon muze byt vice lidsky ten nazev ....
    wrk = arrin
    rrows = G.rr
    rcols = G.rc
    if (reachNA):
        for i in rrows:
            for j in rcols[i]:
                if (fs[i][j] >= 1000):
                    wrk[i][j] = G.NoDataValue
    tools.make_ASC_raster(outName, wrk, G)


#TODO
"""
if Gl.arcgis:
    raster_output = raster_output_Gl.arcgis
else:
"""
raster_output = raster_output_ascii



def do(cumulative, mat_slope, G, surArr):

    output = G.outdir
    rrows = G.rr
    rcols = G.rc

    for i in rrows:
        for j in rcols[i]:
            if cumulative.h_sur[i][j] == 0.:
                cumulative.v_sur[i][j] = 0.
            else:
                cumulative.v_sur[i][j] = cumulative.q_sur[
                    i][j] / cumulative.h_sur[i][j]
            cumulative.shear_sur[i][j] = cumulative.h_sur[
                i][j] * 98.07 * mat_slope[i][j]

    # 1, 2, 15, 16
    main_output = [1, 2, 6, 7, 15, 16]
        # jj vyznam najdes v class Cumulative mezi class Cumulative a
        # def__init__

    if Gl.subflow:
        main_output += [14, 15, 16, 17, 18]
    if Gl.extraOut:  # jj tady jen pokud chceme se i ten zbytek Gl.extraOut je zatim definovan  na zacatku class_main_arrays
        main_output += [4, 8, 9, 11, 12, 13, 14]

    finState = np.zeros(np.shape(surArr), int)
    finState.fill(G.NoDataValue)
    vRest = np.zeros(np.shape(surArr), float)
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
            if (finState[i][j] >= 1000):
                vRest[i][j] = G.NoDataValue
            else:
                vRest[i][j] = surArr[i][j].h_total_new * G.pixel_area

    totalBil = (cumulative.precipitation + cumulative.inflow_sur) - (cumulative.infiltration +
                                                                     cumulative.v_sur + cumulative.v_rill) - cumulative.sur_ret  # + (cumulative.v_sur_r + cumulative.v_rill_r)
    totalBil -= vRest

    raster_output(totalBil, G, finState, 'massBalance')
    raster_output(finState, G, finState, 'reachfid', False)
    raster_output(vRest, G, finState, 'volrest_m3')

    if not(Gl.extraOut):
        if os.path.exists(output + os.sep + 'temp'):
            shutil.rmtree(output + os.sep + 'temp')
        if os.path.exists(output + os.sep + 'temp_dp'):
            shutil.rmtree(output + os.sep + 'temp_dp')
        return 1

### TODO
# if Gl.isStream and Gl.arcgis:
#     import arcpy

#     def write_stream_table(outDir, surface, toky):
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
#                         str(surface.reach[iReach].v_rest) + sep + \
#                           str(surface.reach[iReach].to_node) + '\n'

#                 f.write(line)

#         arcpy.MakeFeatureLayer_management(toky, outTemp + "Gl.streamtmp.shp")
#         arcpy.AddJoin_management(
#             outTemp +
#             "Gl.streamtmp.shp",
#             "FID",
#             outFile,
#             "FID")
#         arcpy.CopyFeatures_management(outTemp + "Gl.streamtmp.shp", outFileShp)

#     stream_table = write_stream_table


# elif Gl.isStream and not(Gl.arcgis):
#     def write_stream_table(outDir, surface, toky):
#         sep = ';'
#         nReaches = surface.nReaches
#         outFile = outDir + 'hydReach.txt'
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
#                     str(surface.reach[iReach].V_out_cum) + sep +   \
#                       str(surface.reach[iReach].Q_max) + sep + str(surface.reach[iReach].timeQ_max)  + sep + str(surface.reach[iReach].h_max) + sep + \
#                         str(surface.reach[iReach].V_rest) + sep + \
#                         str(surface.reach[iReach].to_node) + '\n'

#                 f.write(line)

#     stream_table = write_stream_table

# else:

def pass_stream_table(outDir, surface, toky):
    pass

stream_table = pass_stream_table

