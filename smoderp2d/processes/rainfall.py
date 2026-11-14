# Created by Jan Zajicek, FCE, CTU Prague, 2012-2013

import sys
import numpy as np
import numpy.ma as ma

from smoderp2d.providers import Logger
from smoderp2d.core.general import GridGlobals
from smoderp2d.exceptions import RainDataError

def load_precipitation(fh):
    """TODO.

    :param fh: TODO
    :return: TODO
    """
    y2 = 0
    try:
        fh = open(fh, "r")
        x = []
        for line in fh.readlines():
            split_line = line.split()
            if len(split_line) == 0 or '#' in split_line[0]:
                # row is empty or there is a comment
                continue

            try:
                timestamp = float(split_line[0])
                precipitation = float(split_line[1])
            except ValueError:
                # probaby comma used to separate decimal part
                timestamp = float(split_line[0].replace(',', '.'))
                precipitation = float(split_line[1].replace(',', '.'))

            if (timestamp == 0) & (precipitation > 0):
                # if the record start with zero minutes the line has to
                # be corrected
                raise RainDataError('Rainfall record starts with the length of the '
                                    'first time interval. See the manual.')
            elif (timestamp == 0) & (precipitation == 0):
                # if the record start with zero minutes and rainfall
                # the line is ignored
                continue
            else:
                y0 = timestamp * 60.0  # convert minutes to seconds
                y1 = precipitation / 1000.0  # convert mm to m
                if y1 < y2:
                    raise RainDataError('Rainfall record has to be cumulative')
                y2 = y1
                mv = y0, y1
                x.append(mv)
        fh.close()

        # Values ordered by time ascending
        dtype = [('cas', float), ('value', float)]
        val = np.array(x, dtype=dtype)
        x = np.sort(val, order='cas')
        # Test if time is more than once the same
        state = 0
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

        # for  i, item in enumerate(sr):
        return sr, itera

    except IOError:
        raise RainDataError("The rainfall file does not exist")
    except Exception as e:
        raise RainDataError("Unexpected error: {}".format(e))


def timestepRainfall(itera, total_time, delta_t, tz, sr):
    """Return a rainfall amount for current time step.

    If two or more rainfall records belongs to one time step the function
    integrates the rainfall amount.

    :param itera: TODO
    :param total_time: TODO
    :param delta_t: current time step length
    :param tz: TODO
    :param sr: TODO
    :return: TODO
    """
    z = tz
    # skontroluje jestli neni mimo srazkovy zaznam
    if z > (itera - 1):
        rainfall = 0
    else:
        # skontroluje jestli casovy krok, ktery prave resi, je stale vramci
        # srazkoveho zaznamu z

        if ma.all(sr[z][0] >= (total_time + delta_t)):
            rainfall = sr[z][1] * delta_t
        # kdyz je mimo tak
        else:
            # dopocita zbytek ze zaznamu z, ktery je mezi total_time a
            # total_time + delta_t
            rainfall = sr[z][1] * (sr[z][0] - total_time)
            # skoci do dalsiho zaznamu
            z += 1
            # koukne jestli ten uz neni mimo
            if z > (itera - 1):
                rainfall += 0
            else:
                # pokud je total_time + delta_t stale dal nez konec posunuteho
                # zaznamu vezme celou delku zaznamu a tuto srazku pricte
                while ma.any(sr[z][0] <= (total_time + delta_t)):
                    rainfall += ma.where(
                        sr[z][0] <= (total_time + delta_t),
                        sr[z][1] * (sr[z][0] - sr[z - 1][0]),
                        0
                    )
                    z += 1
                    if z > (itera - 1):
                        break
                # nakonec pricte to co je v poslednim zaznamu kde je
                # total_time + delta_t pred konce zaznamu
                # nebo pricte nulu pokud uz tam zadny zaznam neni
                if z > (itera - 1):
                    rainfall += 0
                else:
                    rainfall += sr[z][1] * (
                            total_time + delta_t - sr[z - 1][0])

            tz = z

    return rainfall, tz


def current_rain(rain, rainfallm, sum_interception):
    """TODO.

    :param rain: TODO
    :param rainfallm: TODO
    :param sum_interception: TODO
    :return: TODO
    """
    # jj
    rain_veg = rain.veg
    rain_ppl = rain.ppl
    rain_pi = rain.pi
    sum_interception_pre = ma.copy(sum_interception)

    interc = rain_ppl * rainfallm  # interception is constant

    sum_interception += ma.where(
        ma.logical_not(rain_veg),
        interc,
        0
    )
    NS = ma.where(
        ma.logical_not(rain_veg),
        ma.where(
            sum_interception >= rain_pi,
            rainfallm - (rain_pi - sum_interception_pre),
            # rest of interception, netto rainfallm
            rainfallm - interc  # netto rainfallm
        ),
        rainfallm
    )
    rain_veg = ma.where(
        ma.logical_and(ma.logical_not(rain_veg), sum_interception >= rain_pi),
        True,  # as vegetation, interception is full
        rain_veg
    )

    if isinstance(NS, int):
        pass

    return NS, sum_interception, rain_veg
