import sys
import numpy as np
import os
from   smoderp2d.src.tools.tools  import comp_type
import smoderp2d.src.io_functions.prt as prt
from   smoderp2d.src.tools.tools  import get_argv
import smoderp2d.src.constants        as constants

extraout = get_argv(constants.PARAMETER_EXTRA_OUTPUT)
rill, subflow, stream, diffuse = comp_type()


class Hydrographs:
  def __init__(self,array_points,outdirr,mat_tok_usek,rr,rc,pixel_area):
    points = array_points
    ipi    = points.shape[0]
    jpj    = 5
    point_int = [[0]*jpj for i in range(ipi)]

    self.inSurface = []
    self.inStream = []
    
    
    
    for ip in range(ipi):
      for jp in [0,1,2]:
        point_int[ip][jp] = int(points[ip][jp])

    for ip in range(ipi):
      for jp in [3,4]:
        point_int[ip][jp] = points[ip][jp]


    #for ttt in point_int:
      #print ttt

    # tento cylkus meze budy, ktere jsou
    # v i,j cylku o jednu vedle rrows a rcols
    outsideDomain = False
    del_=[]
    for ip in range(ipi):
      l = point_int[ip][1]
      m = point_int[ip][2]
      for ipp in rr:
        if l==ipp:
          for jpp in rc[ipp]:
            if m == jpp:
              outsideDomain = True
      if not(outsideDomain) :
        del_.append(ip)
      outsideDomain = False
    point_int = [i for j, i in enumerate(point_int) if j not in del_]
    ipi -= len(del_)


    #for ttt in point_int:
      #print ttt




    #for ip in range(ipi):
      #l = point_int[ip][1]
      #m = point_int[ip][2]
      #print mat_tok_usek[ip][jp]





    counter = 0
    if (mat_tok_usek != None) and (stream == True):
      for ip in range(ipi):
        l = point_int[ip][1]
        m = point_int[ip][2]
        #print mat_tok_usek[ip][jp]
        if mat_tok_usek[l][m] >= 1000:
          self.inStream.append(counter)
          counter += 1
        else:
          self.inSurface.append(counter)
          counter += 1
    else:
      self.inSurface = [i for i in range(ipi)]

    self.inStream.append(-99)
    self.inSurface.append(-99)

    self.n         = ipi
    self.point_int = point_int
    self.subflow = subflow
    self.rill    = rill
    self.stream  = stream
    self.pixel_area = pixel_area
    #print self.point_int
    #raw_input()

    iStream  = 0
    iSurface = 0

    self.header = []

    for i in range(self.n):

      if i == self.inStream[iStream]:

        header = '# Hydrograph at the point with coordinates: '+ str(self.point_int[i][3]) + ' ' + str(self.point_int[i][4]) + '\n'
        header +=  '# A pixel size is [m2]:\n'
        header +=  '# '+str(self.pixel_area) + '\n'

        if not(extraout) :
          header  += '# time[s];deltaTime[s];rainfall[m];reachWaterLevel[m];reachFlow[m3/s];reachVolRunoff[m3]\n'
        else :
          header += '# Time[s];deltaTime[s];Rainfall[m];Waterlevel[m];V_runoff[m3];Q[m3/s];V_from_field[m3];V_rests_in_stream[m3]\n'
        self.header.append(header)
        iStream += 1


      elif i == self.inSurface[iSurface]:
        header = '# Hydrograph at the point with coordinates: '+ str(self.point_int[i][3]) + ' ' + str(self.point_int[i][4]) + '\n'
        header +=  '# A pixel size is [m2]:\n'
        header +=  '# '+str(self.pixel_area) + '\n'


        if not(extraout) :
          header  += '# time[s];deltaTime[s];rainfall[m];totalWaterLevel[m];surfaceFlow[m3/s];surfaceVolRunoff[m3]'
        else :
          header += '# Time[s];deltaTime[s];Rainfall[m];Water_level_[m];Sheet_Flow[m3/s];Sheet_V_runoff[m3];Sheet_V_rest[m3];Infiltration[m];Surface_retetion[m];State;V_inflow[m3];WlevelTotal[m]'

          if rill :
            header += ';WlevelRill[m];Rill_width[m];Rill_flow[m3/s];Rill_V_runoff[m3];Rill_V_rest;Surface_Flow[m3/s];Surface_V_runoff[m3]'
          header += ';SurfaceBil[m3]'
          if subflow :
            header += ';Sub_Water_level_[m];Sub_Flow_[m3/s];Sub_V_runoff[m3];Sub_V_rest[m3];Percolation[];exfiltration[]'
          if extraout :
            header += ';V_to_rill.m3.;ratio;courant;courantrill;iter'

        header += '\n'
        iSurface += 1
        self.header.append(header)




    self.files = []
    for i in range(self.n):
      name_ = outdirr+os.sep+'point'+str(self.point_int[i][0]).zfill(3)+'.dat'
      file_ = open(name_,'w')
      file_.writelines(self.header[i])
      self.files.append(file_)



    del self.inStream[-1]
    del self.inSurface[-1]

    prt.message("Hydrographs files has been created...")



  def write_hydrographs_record(self,i,j,ratio,courant,courantRill,iter_,dt,total_time,surface,subsurface,currRain,inStream=False,sep=';'):

    if inStream :
      for ip in self.inStream:
        l = self.point_int[ip][1]
        m = self.point_int[ip][2]
        line = str(total_time) + sep
        line += str(dt) + sep
        line += str(currRain) + sep
        line += surface.return_stream_str_vals(l,m,sep,dt,extraout)
        line += '\n'
        self.files[ip].writelines(line)







    else:
      for ip in self.inSurface:
        l = self.point_int[ip][1]
        m = self.point_int[ip][2]
        if i == l and j == m:
          line = str(total_time) + sep
          line += str(dt) + sep
          line += str(currRain) + sep
          linebil = surface.return_str_vals(l,m,sep,dt,extraout)
          line += linebil[0] # + sep
          line += str(linebil[1]) # + sep
          #line += subsurface.return_str_vals(l,m,sep,dt) + sep   # prozatim
          if extraout :
            line += sep + str(surface.arr[l][m].V_to_rill) + sep
            line += str(ratio) + sep
            line += str(courant) + sep
            line += str(courantRill) + sep
            line += str(iter_)

          line += '\n'
          self.files[ip].writelines(line)

  #def write_hydrographs_usek(self,dt,total_time,surface,currRain,sep=';'):
    #line = str(total_time) + sep
    #line += str(dt) + sep
    #line += str(currRain) + sep
    #line += surface.return_stream_str_vals(0,0,sep,dt)
    #line += '\n'
    #self.tokusek.writelines(line)


  def closeHydrographs(self):
    for i in range(self.n):
      self.files[i].close()



class HydrographsPass:
  def write_hydrographs_record(self,i,j,ratio,courant,courantRill,iter_,dt,total_time,surface,subsurface,currRain,inStream=False,sep=';'):
    pass
  def closeHydrographs(self):
    pass



