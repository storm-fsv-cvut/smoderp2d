# @package smoderp2d.stream_functions.stream_f Module to calculate the stream reaches runoff.

import math
import sys
from inspect import currentframe, getframeinfo

from smoderp2d.providers import Logger

# Jen na debug, umi to zjistit nazev souboru a radek odkud se\n
#  <em>print frameinfo.filename, frameinfo.lineno</em>\n
#  tiskne
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
#
def compute_h(A, m, b, err=0.0001, max_iter=20):
    def feval(h):
        return b * h + m * h * h - A

    def dfdheval(h):
        return b + 2.0 * m * h
    # prvni odhad vysky
    h_pre = A / b
    h = h_pre
    iter_ = 1
    while (feval(h_pre) > err):
        h = h_pre - feval(h_pre) / dfdheval(h_pre)
        h_pre = h
        if iter_ >= max_iter:
            Logger.error(
                "if file %s %s %s %s %s %s %s %s",
                frameinfo.filename,
                "near line ",
                frameinfo.lineno,
                "\n\t newton solver didnt converge after",
                max_iter,
                'iterations (max_iter=',
                max_iter,
                ')')
            break
        iter_ += 1
    # print 'check', A, b*h+m*h*h
    return h


# Function calculates the discharge in rectangular shaped reach of a stream.
#
#
def rectangle(reach, dt):
    Vp = reach.q365 * dt                # objem           : baseflow
    hp = Vp / (reach.b * reach.length)    # vyska hladiny   : baseflow
    dV = reach.V_in_from_field + reach.vol_rest + \
        reach.V_in_from_reach    # z okoli, predtim, odtok  : epizoda
    h = dV / (reach.b * reach.length)  # vyska hladiny   : epizoda
    H = hp + h                        # total vyska hl. : epizoda
    O = reach.b + 2 * H  # omoceny obvod
    S = reach.b * H    # prurocna plocha
    R = S / O          # hydraulicky polomer
    reach.vs = math.pow(
        R,
        0.6666) * math.pow(
        reach.slope,
         0.5) / (
            reach.roughness)  # rychlost
    reach.Q_out = S * \
        reach.vs  # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt                   # prutok
    reach.V_out = reach.Q_out * \
        dt                                               # odtekly objem
    if reach.V_out > dV:
        reach.V_out = dV
        reach.Q_out = dV / dt
        reach.vol_rest = 0.0
    else:
        reach.Q_out = reach.V_out / dt
        reach.vol_rest = dV - reach.V_out  # V_zbyt
    reach.h = H


def trapezoid(reach, dt):
    """Calculates the discharge in trapezoidal shaped reach of a
    stream.

    :param reach: ?
    :param dt: ?
    """
    Vp = reach.q365 * dt
    hp = compute_h(A=Vp / reach.length, m=reach.m, b=reach.b)
    B = reach.b + 2.0 * hp * reach.m  # b pro pocatecni stav (q365)
    Bb = B + hp * reach.m
    h = compute_h(
        A=(reach.V_in_from_field + reach.vol_rest +
           reach.V_in_from_reach) / reach.length,
        m=reach.m,
     b=reach.b)
    H = hp + h  # celkova vyska
    O = B + 2.0 * H * math.pow(1 + reach.m * reach.m, 0.5)
    S = B * H + reach.m * H * H
    dS = S - reach.b * hp + reach.m * hp * hp
    dV = dS * reach.length
    R = S / O
    reach.vs = math.pow(R, 0.6666) * math.pow(reach.slope, 0.5) / (reach.roughness)  # v
    reach.Q_out = S * reach.vs  # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt
    if reach.V_out > dV:
        reach.V_out = dV
        reach.Q_out = dV / dt
        reach.vol_rest
    else:
        reach.Q_out = reach.V_out / dt
        reach.vol_rest = dV - reach.V_out  # V_zbyt
    reach.h = H
    
    
    #print reach.V_in_from_field, reach.vol_rest, reach.V_in_from_reach, reach.length
    #raw_input()
    # prt.mujout.writelines(str(reach.id_) + ';' + str(reach.h) + ';' +
    # str(reach.V_in_from_field) + ';' + str(reach.vol_rest) + ';' + str(
    # reach.V_in_from_reach) + ';' + str(reach.V_out) + ';' +
    # str(reach.to_node)+'\n')


# Function calculates the discharge in triangular shaped reach of a stream.
#
#
def triangle(reach, dt):
    pass
    Vp = reach.q365 * \
        dt                             # objem           : baseflow
    hp = math.pow(
        Vp / (reach.length * reach.m),
        0.5)   # vyska hladiny   : baseflow __
    B = 2.0 * hp * \
        reach.m                             # sirka zakladny  : baseflow \/
    # Bb = B + reach.h*reach.m                                                                # tohle nechapu, takze jsem to zakomantoval...
    # h  = (reach.V_in_from_field + reach.vol_rest + reach.V_in_from_reach)/(Bb
    # * reach.length) # tohle nechapu...

    Ve = (
        reach.V_in_from_field +
        reach.vol_rest +
     reach.V_in_from_reach)     # objem z epizody
    #
    # vyska z epizody co pribude na trouhelnik z baseflow (takze lichobeznik)
    #                       ____                                          __
    # zahlacna lichobezniku \__/ je spodni 'horni'  zakladna trojuhelniku \/
    he = compute_h(
        A=Ve / reach.length,
        m=reach.m,
     b=B)  # funkce pouzita pro lichobeznik  ____
    H = hp + \
        he                                     # vyska vysledneho trouhelniku    \  /
    O = 2.0 * H * math.pow(
        1.0 + reach.m * reach.m,
        0.5)  # \/
    S = reach.m * H * H
    # dS = B*reach.h + reach.m*reach.h*reach.h
    # dV = dS*reach.length
    R = S / O
    reach.vs = math.pow(
        R,
        0.6666) * math.pow(
        reach.slope,
         0.5) / (
            reach.roughness)  # v
    reach.Q_out = S * reach.vs  # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt
    if reach.V_out > Ve:
        reach.V_out = Ve
        reach.Q_out = Ve / dt
        reach.vol_rest = 0
    else:
        reach.Q_out = reach.V_out / dt
        reach.vol_rest = Ve - reach.V_out
    reach.h = H


# Function calculates the discharge in parabola shaped reach of a stream.
#
#
def parabola(reach, dt):
    raise NotImplementedError('Parabola shaped stream reach has not \
            been implemented yet')
    # a = reach.b   #vzd ohniska od vrcholu
    # u = 3.0 #(h=B/u  B=f(a))
    # Vp = reach.q365*dt
    # hp = math.pow(Vp*3/(2*reach.length*u),0.5)
    # B = u*hp #sirka hladiny #b = 3*a/(2*h)
    # reach.h = math.pow((reach.V_in_from_field + reach.vol_rest)/(2*reach.length*math.pow(hp,0.5))+math.pow(hp,1.5),0.6666)  # h = (dV/2.L.hp^0,5+hp^1,5)^0,666
    # H = hp + reach.h
    # Bb = u*H
    # O = Bb+8*H*H/(3*Bb)
    # S = 2/3*Bb*H
    # dS = S - 2/3*B*hp
    # dV = dS*reach.length
    # R = S/O
    # reach.Q_out = S*math.pow(R,0.66666)*math.pow(reach.slope,0.5)/(reach.roughness) # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    # reach.V_out = reach.Q_out*dt
    # if reach.V_out > dV:
        # reach.V_out = dV
        # reach.Q_out = dV/dt
    # reach.vs = math.pow(R,0.6666)*math.pow(reach.slope,0.5)/(reach.roughness) #v
    # reach.vol_rest = dV - reach.V_out
    # reach.h = H


# def stream_reach_max(toky):
    # fc = toky
    # field2 = ["FID","V_infl_ce","total_Vic","V_infl","total_Vi","V_outfl","total_Vo","NS","total_NS","Q_outfl","max_Q","h","max_h","vs","max_vs","V_zbyt","total_Vz","V_infl_us", "total_Viu"]
    # with arcpy.da.UpdateCursor(fc, field2) as cursor:
        # for row in cursor:
        # row[2] = row[2] + row[1]
        # cursor.updateRow (row)
        # row[4] = row[4] + row[3]
        # cursor.updateRow (row)
        # row[6] = row[6] + row[5]
        # cursor.updateRow (row)
        # row[8] = row[8] + row[7]
        # cursor.updateRow (row)
        # row[16] = row[16] + row[15]
        # cursor.updateRow (row)
        # row[18] = row[18] + row[17]
        # cursor.updateRow (row)
        # if row[10] < row[9]:
          # row[10] = row[9]
          # cursor.updateRow (row)
        # if row[12] < row[11]:
          # row[12] = row[11]
          # cursor.updateRow (row)
        # if row[14] < row[13]:
          # row[14] = row[13]
          # cursor.updateRow (row)


# def safe_outflows(toky):
    # if type_of_computing == 3:
        # fc = toky
        # field3 = ["V_outfl","V_outfl_tm","V_zbyt","V_zbyt_tm"]
        # with arcpy.da.UpdateCursor(fc, field3) as cursor:
        # for row in cursor:
          # row[1] = row[0]
          # cursor.updateRow (row)
          # row[3] = row[2]
          # cursor.updateRow (row)
