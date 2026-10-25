# @package smoderp2d.stream_functions.stream_f Module to calculate the stream reaches runoff.

import numpy.ma as ma
import numpy as np
import math

from inspect import currentframe, getframeinfo

from smoderp2d.providers import Logger

frameinfo = getframeinfo(currentframe())


# Newton method to compute water level in trapezoidal reach,
#
#   \f[
#   h_{n+1} = h_{n} - \frac{f(h_n)}{f^{\prime}(h_n)}
#   \f]
#   \f[
#      f(h) = bh+mh^2 - A
#   \f]
#   \f[
#      f^{\prime}(h) = b+2mh
#   \f]
#
#   @return h water level in the trapezoid


def compute_h(A, m, b, err=0.0001, max_iter=20, hinit = 100):
    def feval(h):
        return b * h + m * h * h - A

    def dfdheval(h):
        return b + 2.0 * m * h

    # first height estimation
    h_pre = hinit
    h = h_pre
    iter_ = 1
    while ma.any(feval(h_pre) > err):
        h = ma.where(
            feval(h_pre) > err,
            h_pre - feval(h_pre) / dfdheval(h_pre),
            h
        )
        h_pre = ma.copy(h)
        if iter_ >= max_iter:
            Logger.error(
                f"if file {frameinfo.filename} near line {frameinfo.lineno} "
                f"\n\t newton solver did not converge after {max_iter} "
                f"iterations (max_iter={max_iter})"
            )
            break
        iter_ += 1

    return h



# Function calculates the discharge in trapezoid/rectangle/triangle shaped
# reach of a stream.
#
#
def genshape(reach, dt):
    """Calculates the discharge in trapezoid/rectangle/triangle  shaped reach
    of a stream.

    :param reach: one reach of the stream network
    :param dt: current time step length
    """
    # reach.b - channel_bottom_width
    # reach.length - channel_length
    if reach.q365 > 0:
        # volume of baseflow
        vol_baseflow = reach.q365 * dt  
        # water level of baseflow
        h_baseflow = compute_h(
                A=vol_baseflow / reach.length, 
                m=reach.m,
                b=reach.b)
    else:
        # water level of baseflow
        h_baseflow = 0.0

    # baseflow water level width
    #   for trapezoid equals reach.b if h_baseflow = 0.
    #   for traingle equals zero if h_baseflow = 0.
    b_baseflow = reach.b + 2.0 * h_baseflow * reach.m 
    
    # water level increase due rainfall
    h = compute_h(
        A=(reach.V_in_from_field + reach.vol_rest +
           reach.V_in_from_reach) / reach.length,
        m=reach.m,
        b=b_baseflow, hinit = reach.h + 1)
    
    # total water level in reach; baseflow + epizode water 
    H = h_baseflow + h  

    # total wetted perimeter: baseflow + epizode water
    wetted_perimeter = reach.b + 2.0 * H * ma.power(1 + reach.m * reach.m, 0.5)
    # total cross-sectional area of the flow
    cross_section = reach.b * H + reach.m * H * H

    # cross section of the epizode water
    dcross_section = cross_section - reach.b * h_baseflow + reach.m * \
    h_baseflow * h_baseflow

    # volume of the epizode water
    dvol = dcross_section * reach.length
    # hydraulic diameter
    hyd_diameter = cross_section / wetted_perimeter

    # calculated velocity based on mannings
    reach.vs = ma.power(
        hyd_diameter,
        0.6666) * ma.power(
        reach.inclination,
        0.5) / (reach.roughness)  

    # calculated outflow m3/s
    reach.Q_out = cross_section * reach.vs  
    # calculated outflow volume m3
    reach.V_out = reach.Q_out * dt

    if reach.V_out > dvol:
        # outflow volumw is saved to reach class
        reach.V_out = dvol
        # what rests in stream reach after time step calculation is completed
        reach.vol_rest = 0
    else:
        # what rests in stream reach after time step calculation is completed
        reach.vol_rest = dvol - reach.V_out

    # outflow discharge m3/s is saved to reach class
    reach.Q_out = reach.V_out / dt
    # total water level in stream reach is saved to reach class
    reach.h = H



# Function calculates the discharge in parabola shaped reach of a stream.
#
#
def parabola(reach, dt):
    # a = reach.b   #vzd ohniska od vrcholu
    u = 3.0 #(h=B/u  B=f(a))
    if reach.q365 > 0:
        Vp = reach.q365 * dt  # objem           : baseflow
        hp = ma.power(Vp * 3 / (2 * reach.length * u), 0.5)
        # vyska hladiny   : baseflow
        reach.h = ma.power(
            (reach.V_in_from_field + reach.vol_rest) / (2 * reach.length * ma.power(hp, 0.5)) + ma.power(hp, 1.5),
            0.6666
        )  # h = (dV/2.L.hp^0,5+hp^1,5)^0,666
    else:
        # Vp == 0.0
        hp = 0.0

    B = u * hp #sirka hladiny #b = 3*a/(2*h)
    H = hp + reach.h  # D -> vyska hladiny
    dB = u * H
    if dB == 0:
        O = 0
    else:
        O = dB + 8 * H * H / (3 * dB)
    S = 2 / 3 * dB * H
    dS = S - 2 / 3 * B * hp
    dV = dS * reach.length
    if O == 0:
        R = 0
    else:
        R = S / O
    reach.Q_out = S * ma.power(R, 0.66666) * ma.power(reach.inclination, 0.5) / (reach.roughness) # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt

    if reach.V_out > dV:
        reach.Q_out = dV / dt
        reach.V_out = dV
        
    reach.vs = ma.power(R, 0.6666) * ma.power(reach.inclination, 0.5) / (reach.roughness) #v
    reach.vol_rest = dV - reach.V_out
    reach.h = H

# def stream_reach_max(toky):
#     ToDo - tohle asi zachovavalo maxima a pridavalo je to do output vrstvy
#      toku, nevim jestli tuto funkcionalitu prevzala nejaka jina cast kodu.
#     fc = toky
#     field2 = ["FID","V_infl_ce","total_Vic","V_infl","total_Vi","V_outfl","total_Vo","NS","total_NS","Q_outfl","max_Q","h","max_h","vs","max_vs","V_zbyt","total_Vz","V_infl_us", "total_Viu"]
#     with arcpy.da.UpdateCursor(fc, field2) as cursor:
#         for row in cursor:
#         row[2] = row[2] + row[1]
#         cursor.updateRow (row)
#         row[4] = row[4] + row[3]
#         cursor.updateRow (row)
#         row[6] = row[6] + row[5]
#         cursor.updateRow (row)
#         row[8] = row[8] + row[7]
#         cursor.updateRow (row)
#         row[16] = row[16] + row[15]
#         cursor.updateRow (row)
#         row[18] = row[18] + row[17]
#         cursor.updateRow (row)
#         if row[10] < row[9]:
#           row[10] = row[9]
#           cursor.updateRow (row)
#         if row[12] < row[11]:
#           row[12] = row[11]
#           cursor.updateRow (row)
#         if row[14] < row[13]:
#           row[14] = row[13]
#           cursor.updateRow (row)


# def safe_outflows(toky):
#     if type_of_computing == 3:
#         fc = toky
#         field3 = ["V_outfl","V_outfl_tm","V_zbyt","V_zbyt_tm"]
#         with arcpy.da.UpdateCursor(fc, field3) as cursor:
#         for row in cursor:
#           row[1] = row[0]
#           cursor.updateRow (row)
#           row[3] = row[2]
#           cursor.updateRow (row)
