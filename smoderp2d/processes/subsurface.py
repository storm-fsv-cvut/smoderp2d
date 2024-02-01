def relative_unsat_conductivity(S, l, m):

    return S**l * (1.0 - (1.0 - S**(1.0 / m))**m)**2.0


def darcy(sub, effect_vrst):
    Ks = sub.Ks
    h = sub.h
    poro = sub.poro
    slope = sub.slope
<<<<<<< HEAD
    return (Ks * h * efect_vrst * slope)/poro
=======
    return Ks * h * effect_vrst * slope
>>>>>>> master
