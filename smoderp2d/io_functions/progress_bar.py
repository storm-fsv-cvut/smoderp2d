import smoderp2d.constants as constants
from smoderp2d.tools.tools import get_argv
import smoderp2d.io_functions.prt as prt
import time


class CPROG:

    def __init__(self):
        self.pre = 0
        self.startTime = time.time()

    def update(self, i, dt, iter_, total_time):
        # print i
        # i = round(i)
        if i == 0.0:
            # prt.message("-----------------------------------------------------------")
            # prt.message("Total time = ", 0.0, "| time step  = ", "%.2f" % round(dt, 3) , "    | time iterations = ", iter_ )
            # prt.message("{:10.4f}".format(i) + " %", 'is done       | time to
            # end = ??? s')
            prt.message("Total time [s]:   0.0")
            prt.message("Time step  [s]:  ", "%.2f" % dt)
            prt.message("Time iterations: ", iter_)
            prt.message("Percentage done: ", "%.2f" % i + " %")
            prt.message("Time to end [s]:  ???")
            prt.message("--------------------------")
        else:
            self.pre = i
            self.currTime = time.time()
            diffTime = self.currTime - self.startTime
            remaining = (100.0 * diffTime) / i - diffTime
            prt.message("Total time [s]:  ", "%.2f" % total_time)
            prt.message("Time step  [s]:  ", "%.2f" % dt)
            prt.message("Time iterations: ", iter_)
            prt.message("Percentage done: ", "%.2f" % i + " %")
            prt.message("Time to end [s]: ", "%.2f" % remaining)
            prt.message("--------------------------")


pb = CPROG()
