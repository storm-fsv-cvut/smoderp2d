import numpy as np

from smoderp2d.core.general import GridGlobals


def shallowSurfaceKinematic(a, b, h_sheet):
    # numpy.ma removal. This looked like a one-liner but is not: h_sheet
    # holds the no-data value (-9999) outside the computation area, and b
    # used to be a MaskedArray. ma.power() computes
    #     np.where(mask_or(mask(h_sheet), mask(b)), h_sheet, h_sheet ** b)
    # so the mask of b made it put the RAW h_sheet back into .data outside
    # the area instead of evaluating (-9999) ** b. A plain
    # np.power(h_sheet, b) would yield nan there, and that nan does not
    # stay put: vol_runoff derived from it feeds the inflow stencil in
    # D8.inflow_all(), where 0 * nan == nan would poison cells inside the
    # area as well.
    #
    # The behaviour is therefore reproduced explicitly: outside the area
    # return h_sheet unchanged, inside it evaluate the power. Bit-identical
    # to the masked version, and no nan is produced anywhere.
    a = np.asarray(a)
    b = np.asarray(b)
    h_sheet = np.asarray(h_sheet)

    valid = GridGlobals.valid
    if valid is None:
        return np.power(h_sheet, b) * a

    base = ~np.asarray(valid, dtype=bool)
    safe = np.where(base, 1.0, h_sheet)
    return np.where(base, h_sheet, np.power(safe, b) * a)
