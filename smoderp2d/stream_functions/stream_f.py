# @package smoderp2d.stream_functions.stream_f Module to calculate the stream reaches runoff.

import numpy.ma as ma

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


def compute_h(A, m, b, err=0.0001, max_iter=20):
    def feval(h):
        return b * h + m * h * h - A

    def dfdheval(h):
        return b + 2.0 * m * h

    # first height estimation
    h_pre = ma.where(b != 0, A / b, 0)
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


# Function calculates the discharge in rectangular shaped reach of a stream.
#
#
def rectangle(reach, dt):
    if reach.q365 > 0:
        Vp = reach.q365 * dt  # objem           : baseflow
        hp = Vp / (reach.b * reach.length)  # vyska hladiny   : baseflow
    else:
        # Vp == 0.0
        hp = 0.0

    dV = reach.V_in_from_field + reach.vol_rest + \
         reach.V_in_from_reach  # z okoli, predtim, odtok  : epizoda
    # Question ToDo nevim co je V_in_from_field - odhaduji, ze to je pritok
    #  z plosneho odotku prislusnych pixelu v danem casovem kroku pro dany
    h = dV / (reach.b * reach.length)  # vyska hladiny   : epizoda
    H = hp + h  # total vyska hl. : epizoda
    O = reach.b + 2 * H  # omoceny obvod
    S = reach.b * H  # prurocna plocha
    R = S / O  # hydraulicky polomer
    reach.vs = ma.power(
        R,
        0.6666) * ma.power(
        reach.inclination,
        0.5) / (
                   reach.roughness)  # rychlost
    reach.Q_out = S * reach.vs
    # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt                   # prutok
    reach.V_out = reach.Q_out * dt  # odtekly objem
    condition = ma.greater(reach.V_out, dV)
    reach.V_out = ma.where(condition, dV, reach.V_out)
    reach.vol_rest = ma.where(condition, 0, dV - reach.V_out)
    reach.Q_out = reach.V_out / dt
    reach.h = H


def trapezoid(reach, dt):
    """Calculates the discharge in trapezoidal shaped reach of a
    stream.

    :param reach: ?
    :param dt: ?
    """
    if reach.q365 > 0:
        Vp = reach.q365 * dt  # objem           : baseflow
        hp = compute_h(A=Vp / reach.length, m=reach.m, b=reach.b)
        # vyska hladiny   : baseflow
    else:
        # Vp == 0.0
        hp = 0.0

    # explanation: hp = d
    #              B = wetted perimeter, p
    #              reach.m = sqrt(1+Z^2)
    B = reach.b + 2.0 * hp * reach.m  # b pro pocatecni stav (q365)
    # Bb = B + hp * reach.m
    h = compute_h(
        A=(reach.V_in_from_field + reach.vol_rest +
           reach.V_in_from_reach) / reach.length,
        m=reach.m,
        b=reach.b)
    # tuhle iteracni metodu nezna ToDo - nevim kdo ji kdy tvoril
    H = hp + h  # celkova vyska
    O = B + 2.0 * H * ma.power(1 + reach.m * reach.m, 0.5)
    S = B * H + reach.m * H * H
    dS = S - reach.b * hp + reach.m * hp * hp
    dV = dS * reach.length
    R = S / O
    reach.vs = ma.power(R, 0.6666) * ma.power(reach.inclination,
                                              0.5) / reach.roughness
    # v ToDo and Question - proc tady mame 3/5 a 1/2 cislem a ne zlomkem
    reach.Q_out = S * reach.vs  # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt

    condition = ma.greater(reach.V_out, dV)
    reach.V_out = ma.where(condition, dV, reach.V_out)
    reach.vol_rest = ma.where(condition, 0, dV - reach.V_out)
    reach.Q_out = reach.V_out / dt
    reach.h = H

    # prt.mujout.writelines(str(reach.id_) + ';' + str(reach.h) + ';' +
    # str(reach.V_in_from_field) + ';' + str(reach.vol_rest) + ';' + str(
    # reach.V_in_from_reach) + ';' + str(reach.V_out) + ';' +
    # str(reach.to_node)+'\n')


# Function calculates the discharge in triangular shaped reach of a stream.
#
#
def triangle(reach, dt):
    if reach.q365 > 0:
        Vp = reach.q365 * dt  # objem           : baseflow
        hp = ma.power(Vp / (reach.length * reach.m), 0.5)
        # vyska hladiny   : baseflow
    else:
        # Vp == 0.0
        hp = 0.0

    # explanation: hp = d
    #              B = wetted perimeter, p
    #              reach.m = sqrt(1+Z^2)
    B = 2.0 * hp * reach.m
    # sirka zakladny  : baseflow \/
    # Bb = B + reach.h*reach.m
    # tohle nechapu, takze jsem to zakomantoval...
    # h  = (reach.V_in_from_field + reach.vol_rest + reach.V_in_from_reach)/(Bb
    # * reach.length) # tohle nechapu...

    Ve = (reach.V_in_from_field + reach.vol_rest + reach.V_in_from_reach)
    # objem z epizody
    #
    # vyska z epizody co pribude na trouhelnik z baseflow (takze lichobeznik)
    #                       ____                                          __
    # zakladna lichobezniku \__/ je spodni 'horni'  zakladna trojuhelniku \/
    he = compute_h(A=Ve / reach.length, m=reach.m, b=B)
    # funkce pouzita pro lichobeznik  ____
    H = hp + he
    # vyska vysledneho trouhelniku    \  /
    O = 2.0 * H * ma.power(
        1.0 + reach.m * reach.m,
        0.5)  # \/
    S = reach.m * H * H
    # dS = B*reach.h + reach.m*reach.h*reach.h
    # dV = dS*reach.length
    R = ma.where(O != 0, S / O, 0)
    reach.vs = ma.power(
        R,
        0.6666) * ma.power(
        reach.inclination,
        0.5) / (reach.roughness)  # v
    reach.Q_out = S * reach.vs  # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt

    condition = ma.greater(reach.V_out, Ve)
    reach.V_out = ma.where(condition, Ve, reach.V_out)
    reach.vol_rest = ma.where(condition, 0, Ve - reach.V_out)
    reach.Q_out = reach.V_out / dt
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
    O = ma.where(dB != 0, dB + 8 * H * H / (3 * dB), 0)
    S = 2 / 3 * dB * H
    dS = S - 2 / 3 * B * hp
    dV = dS * reach.length
    R = ma.where(O != 0, S / O, 0)
    reach.Q_out = S * ma.power(R, 0.66666) * ma.power(reach.inclination, 0.5) / (reach.roughness) # Vo=Qo.dt=S.R^2/3.i^1/2/(n).dt
    reach.V_out = reach.Q_out * dt

    reach.Q_out = ma.where(reach.V_out > dV, dV / dt, reach.Q_out)
    reach.V_out = ma.where(reach.V_out > dV, dV, reach.V_out)
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
