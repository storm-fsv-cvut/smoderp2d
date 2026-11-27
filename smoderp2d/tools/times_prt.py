import os
from smoderp2d.providers import Logger

from smoderp2d.core.general import Globals


class TimesPrt(object):
    """TODO."""
    def __init__(self):
        if not Globals.prtTimes:
            self.fTimes = None
            return

        self.fTimes = open(Globals.prtTimes, 'r')
        self.outsubrid = 'prubeh'
        os.makedirs(os.path.join(Globals.outdir, self.outsubrid))

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

    def prt(self, time, dt, sur):
        """TODO.

        :param time: TODO
        :param dt: current time step length
        :param sur: TODO
        """
        if not self.fTimes:
            return

        if self.__n == len(self.times):
            return

        if (time < self.times[self.__n]) and (self.times[self.__n] <= time + dt):
            cas = '%015.2f' % (time + dt)
            filein = os.path.join(
                Globals.outdir, self.outsubrid,
                'H' + str(cas).replace('.', '_') + '.asc'
            )
            Logger.info("Printing total H into file {}".format(filein))

            tmp = sur.arr.h_total_new

            make_ASC_raster(filein, tmp, Globals)

            # pro pripat, ze v dt by bylo vice pozadovanych tisku,
            # v takovem pripade udela jen jeden
            # a skoci prvni cas, ktery je mimo
            while (time < self.times[self.__n]) and (self.times[self.__n] <= time + dt):
                self.__n += 1
                if self.__n == len(self.times):
                    return
