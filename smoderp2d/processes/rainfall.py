#!/usr/bin/python
# -*- coding: latin-1 -*-
# SMODERP 2D
# Created by Jan Zajicek, FCE, CTU Prague, 2012-2013

import sys
import numpy as np

from smoderp2d.providers import Logger

# definice erroru  na urovni modulu
#


class Error(Exception):

    """Base class for exceptions in this module."""
    pass


class NonCumulativeRainData(Error):

    """Exception raised bad rainfall record assignment.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self):
        self.msg = 'Error: Rainfall record has to be cumulative'

    def __str__(self):
        return repr(self.msg)


class ErrorInRainfallRecord(Error):

    """Exception raised for  rainfall record assignment.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self):
        self.msg = 'Error: Rainfall record starts with the length of the first time interval. See manual.'

    def __str__(self):
        return repr(self.msg)
    
    
def load_precipitation(fh):
    y2 = 0
    try:
        fh = open(fh, "r")
        x = []
        for line in fh.readlines():
            z = line.split()
            if len(z) == 0:
                continue
            elif z[0].find('#') >= 0:
                continue
            else:
                if (len(z) == 0) : # if raw in text file is empty
                    continue
                elif ((float(z[0])==0) & (float(z[1])>0)) : # if the record start with zero minutes the line has to be corrected
                    raise ErrorInRainfallRecord()
                elif ((float(z[0])==0) & (float(z[1])==0)) : # if the record start with zero minutes and rainfall the line is ignored
                    continue
                else:
                    y0 = float(z[0]) * 60.0  # prevod na vteriny
                    y1 = float(z[1]) / 1000.0  # prevod na metry
                    if y1 < y2:
                        raise NonCumulativeRainData()
                    y2 = y1
                    mv = y0, y1
                    x.append(mv)
        fh.close

        # Values ordered by time ascending
        dtype = [('cas', float), ('value', float)]
        val = np.array(x, dtype=dtype)
        x = np.sort(val, order='cas')
        # Test if time time is more than once the same
        state = 0
        k = 1
        itera = len(x)  # iter is needed in main loop
        for k in range(itera):
            if x[k][0] == x[k - 1][0] and itera != 1:
                state = 1
                y = np.delete(x, k, 0)

        if state == 0:
            x = x
        else:
            x = y
        # Amount of rainfall in individual intervals
        if len(x) == 0:
            sr = 0
        else:
            sr = np.zeros([itera, 2], float)
            for i in range(itera):
                if i == 0:
                    sr_int = x[i][1] / x[i][0]
                    sr[i][0] = x[i][0]
                    sr[i][1] = sr_int

                else:
                    sr_int = (x[i][1] - x[i - 1][1]) / (x[i][0] - x[i - 1][0])
                    sr[i][0] = x[i][0]
                    sr[i][1] = sr_int

        #for  i, item in enumerate(sr):
            #print item[0], '\t', item[1]
        return sr, itera

    except IOError:
        Logger.critical("The rainfall file does not exist!")
    except:
        Logger.critical("Unexpected error:", sys.exc_info()[0])
        raise


def timestepRainfall(iterace, total_time, delta_t, tz, sr):
    """Function returns a rainfall amount for current time step if two or
       more rainfall records belongs to one time step the function
       integrates the rainfall amount.
    """
    z = tz
    # skontroluje jestli neni mimo srazkovy zaznam
    if z > (iterace - 1):
        rainfall = 0
    else:
        # skontroluje jestli casovy krok, ktery prave resi, je stale vramci
        # srazkoveho zaznamu z

        if sr[z][0] >= (total_time + delta_t):
            rainfall = sr[z][1] * delta_t
        # kdyz je mimo tak
        else:
            # dopocita zbytek ze zaznamu z, ktery je mezi total_time a
            # total_time + delta_t
            rainfall = sr[z][1] * (sr[z][0] - total_time)
            # skoci do dalsiho zaznamu
            z += 1
            # koukne jestli ten uz neni mimo
            if z > (iterace - 1):
                rainfall += 0
            else:
                # pokud je total_time + delta_t stale dal nez konec posunuteho zaznamu
                # vezme celou delku zaznamu a tuto srazku pricte
                while (sr[z][0] <= (total_time + delta_t)):
                    rainfall += sr[z][1] * (sr[z][0] - sr[z - 1][0])
                    z += 1
                    if z > (iterace - 1):
                        break
                # nakonec pricte to co je v poslednim zaznamu kde je total_time + delta_t pred konce zaznamu
                # nebo pricte nulu pokud uz tam zadny zaznam neni
                if z > (iterace - 1):
                    rainfall += 0
                else:
                    rainfall += sr[z][1] * (
                        total_time + delta_t - sr[z - 1][0])

            tz = z

    return rainfall, tz


def current_rain(rain, rainfallm, sum_interception):
    # jj
    rain_veg = rain.veg
    rain_ppl = rain.ppl
    rain_pi = rain.pi
    sum_interception_pre = sum_interception
    if not rain_veg:
        interc = rain_ppl * rainfallm  # interception is konstant
        sum_interception += interc  # sum of intercepcion

        if sum_interception >= rain_pi:
            # rest of intercetpion
            interc_rest = rain_pi - sum_interception_pre
            NS = rainfallm - interc_rest  # netto rainfallm
            rain_veg = True # as vegetatio interception is full
        else:
            NS = rainfallm - interc  # netto rainfallm
    
    else:
        NS = rainfallm

    return NS, sum_interception, rain_veg
