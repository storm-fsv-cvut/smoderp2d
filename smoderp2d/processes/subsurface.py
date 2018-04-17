def relative_unsat_conductivity(S, l, m):

    return S**l * (1.0 - (1.0 - S**(1.0 / m))**m)**2.0


def darcy(sub, efect_vrst):
    Ks = sub.Ks
    h = sub.h
    slope = sub.slope
    return Ks * h * efect_vrst * slope
