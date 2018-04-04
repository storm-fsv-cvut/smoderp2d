import numpy as np
import os
import smoderp2d.src.constants as constants
from smoderp2d.src.tools.tools import get_argv
from smoderp2d.src.tools.tools import make_ASC_raster
from smoderp2d.src.main_classes.General import *
import smoderp2d.src.io_functions.prt as prt

from smoderp2d.src.main_classes.General import Globals as Gl


if Gl.prtTimes == '-':
    class TimesPrt():

        def __init__(self):
            pass

        def prt(self, time, dt, sur):
            pass
else:
    class TimesPrt():

        def __init__(self):

            self.fTimes = open(Gl.prtTimes, 'r')
            self.outsubrid = 'prubeh'
            os.makedirs(Globals.outdir + os.sep + self.outsubrid)
            self.times = []
            self.__n = 0

            for line in self.fTimes.readlines():
                z = line.split()
                if len(z) == 0:
                    continue
                elif z[0].find('#') >= 0:
                    continue
                else:
                    if len(z) == 0:
                        continue
                    else:
                        self.times.append(float(line) * 60.0)
            self.times.sort()

            print self.times
            raw_input()

        def prt(self, time, dt, sur):
            if self.__n == len(self.times):
                return

            if (time < self.times[self.__n]) & (self.times[self.__n] <= time + dt):

                cas = '%015.2f' % (time + dt)
                filen = Globals.outdir + os.sep  + self.outsubrid + \
                    os.sep + 'H' + str(cas).replace('.', '_') + '.asc'
                prt.message(
                    "Printing total H into file: ." +
                    os.sep +
                    filen +
                    '...')
                prt.message(
                    "-----------------------------------------------------------")
                prt.message(
                    "-----------------------------------------------------------")
                tmp = np.zeros([Globals.r, Globals.c], float)

                for i in Globals.rr:
                    for j in Globals.rc[i]:
                        tmp[i][j] = sur.arr[i][j].h_total_new

                make_ASC_raster(filen, tmp, Globals)

                # pro pripat, ze v dt by bylo vice pozadovanych tisku, v takovem pripade udela jen jeden
                # a skoci prvni cas, ktery je mimo
                while (time < self.times[self.__n]) & (self.times[self.__n] <= time + dt):
                    self.__n += 1
                    if self.__n == len(self.times):
                        return
