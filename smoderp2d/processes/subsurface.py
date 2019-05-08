def relative_unsat_conductivity(S, l, m):

    return S**l * (1.0 - (1.0 - S**(1.0 / m))**m)**2.0


def darcy(sub, mat_efect_cont):
    return sub.Ks * sub.h * mat_efect_cont * \
           sub.slope
