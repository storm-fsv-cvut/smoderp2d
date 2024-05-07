def relative_unsat_conductivity(S, m, l=0.5):
    """
    :param S: subsoil layers saturation.
    :param m: van genuchten parameter 
    :param l: Mualem's parameter, it is usually 0.5
    """
    return S**l * (1.0 - (1.0 - S**(1.0 / m))**m)**2.0
    


def darcy(sub, effect_vrst):
    Ks = sub.Ks
    h = sub.h
    slope = sub.slope
    return Ks * h * effect_vrst * slope
