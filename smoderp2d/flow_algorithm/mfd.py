#!/usr/bin/python
# -*- coding: latin-1 -*-
# SMODERP 2D
# Created by Jan Zajicek, FCE, CTU Prague, 2012-2013

# importing system moduls
import math
import numpy as np
import numpy.ma as ma

from smoderp2d.flow_algorithm.py_dmtfce import neighbors, dirSlope, boolToInt, \
    FB, VE, removeCellsWithSameHeightNeighborhood

from smoderp2d.core.general import GridGlobals
from smoderp2d.providers import Logger


def new_mfda(mat_dem, mat_nan, mat_fd):
    """TODO.

    :param mat_dem: digital elevation model
    :param mat_nan: TODO
    :param mat_fd: flow directions
    """
    state = 0
    state2 = 0

    rows = GridGlobals.r
    cols = GridGlobals.c
    dy = GridGlobals.dy
    dx = GridGlobals.dx

    val_array = ma.masked_array(
        np.zeros([rows, cols, 8], float),
        mask=np.stack((GridGlobals.masks,) * 8, 2)
    )
    val_array2 = ma.masked_array(
        np.zeros([rows, cols], float), mask=GridGlobals.masks
    )
    fd_rill = ma.masked_array(
        np.zeros([rows, cols], float), mask=GridGlobals.masks
    )

    Logger.info("Computing multiple flow direction algorithm...")

    # function determines if cell neighborhood has multiple cell with exactly
    # same values of height, and then it saves that cell as NoData
    mat_dem, mat_nan = removeCellsWithSameHeightNeighborhood(
        mat_dem, mat_nan, rows, cols)

    # main multiple-flow direction algorithm calculation
    for i in range(rows):
        for j in range(cols):

            point_m = mat_dem[i][j]

            if point_m < 0 or i == 0 or j == 0 or i == (rows - 1) or j == (cols - 1):
                # jj nemely by ty byt nuly?
                val_array[i][j][:] = 0  # -3.40282346639e+38
                val_array2[i][j] = -3.40282346639e+38

            else:
                possible_circulation = 0

                nbrs = neighbors(i, j, mat_dem, rows, cols)
                if any([ma.is_masked(nbr) for nbr in nbrs]):
                    continue
                fldir, flsp = dirSlope(point_m, nbrs, dy, dx)

                flprop = np.zeros(8, float)
                sum_slgr = 0

                pc = 0

                # checking for cells with same height as neighbors
                for k in range(8):
                    if abs(point_m - nbrs[k]) < 1e-5:
                        pc += 1

                if pc > 1:
                    possible_circulation = 1
                # circulation is not possible
                if possible_circulation == 0:
                    for k in range(8):
                        slgr = flsp[k]  # slope gradient
                        if slgr < 0:
                            continue
                        else:
                            sum_slgr += math.pow(slgr, VE)
                            # sum of slope gradient
                    if sum_slgr == 0:
                        for m in range(8):
                            if fldir[m] == 0:
                                if m == 0:
                                    val_array[i][j][5] = 1.0
                                    val_array2[i][j] = 32
                                    fd_rill[i][j] = 32
                                if m == 1:
                                    val_array[i][j][6] = 1.0
                                    val_array2[i][j] = 64
                                    fd_rill[i][j] = 64
                                if m == 2:
                                    val_array[i][j][7] = 1.0
                                    val_array2[i][j] = 128
                                    fd_rill[i][j] = 128
                                if m == 3:
                                    val_array[i][j][0] = 1.0
                                    val_array2[i][j] = 1
                                    fd_rill[i][j] = 1
                                if m == 4:
                                    val_array[i][j][1] = 1.0
                                    val_array2[i][j] = 2
                                    fd_rill[i][j] = 2
                                if m == 5:
                                    val_array[i][j][2] = 1.0
                                    val_array2[i][j] = 4
                                    fd_rill[i][j] = 4
                                if m == 6:
                                    val_array[i][j][3] = 1.0
                                    val_array2[i][j] = 8
                                    fd_rill[i][j] = 8
                                if m == 7:
                                    val_array[i][j][4] = 1.0
                                    val_array2[i][j] = 16
                                    fd_rill[i][j] = 16
                        continue
                    else:
                        for k in range(8):
                            slgr = flsp[k]  # slope gradient
                            if slgr < 0:
                                flprop[k] = 0
                            else:
                                fl_prop = math.pow(
                                    slgr,
                                    VE) / sum_slgr  # flow proportions
                                flprop[k] = fl_prop

                    flow_amount_cell = np.zeros(8, float)

                    for l in range(8):

                        flowcells = flprop[l]

                        if flowcells > 0:
                            prop = (fldir[l] / FB) * flowcells
                            # percentage part into 1st cell
                            prop2 = (1 - fldir[l] / FB) * flowcells
                            # to second cell

                            if l == 0 and 0 < fldir[l] < FB:
                                # division to two cells
                                flow_amount_cell[0] = prop2
                                flow_amount_cell[1] = prop
                                state2 = 1  # because of last cell in the loop
                            elif l == 0 and fldir[l] == 0:
                                # only to one cell division
                                flow_amount_cell[0] = flowcells

                            if l == 1 and 0 < fldir[l] < FB:
                                if state2 == 1:
                                    flow_amount_cell[
                                        1] = flow_amount_cell[
                                            1] + prop2
                                else:
                                    flow_amount_cell[1] = prop2
                                flow_amount_cell[2] = prop
                                state = 2
                            elif l == 1 and fldir[l] == 0:
                                flow_amount_cell[1] = flowcells

                            if l == 2 and 0 < fldir[l] < FB:
                                if state == 2:
                                    flow_amount_cell[
                                        2] = flow_amount_cell[
                                            2] + prop2
                                else:
                                    flow_amount_cell[2] = prop2
                                flow_amount_cell[4] = prop
                                state = 3
                            elif l == 2 and fldir[l] == 0:
                                flow_amount_cell[2] = flowcells

                            if l == 3 and 0 < fldir[l] < FB:
                                if state == 3:
                                    flow_amount_cell[
                                        4] = flow_amount_cell[
                                            4] + prop2
                                else:
                                    flow_amount_cell[4] = prop2
                                flow_amount_cell[7] = prop
                                state = 4
                            elif l == 3 and fldir[l] == 0:
                                flow_amount_cell[4] = flowcells

                            if l == 4 and 0 < fldir[l] < FB:
                                if state == 4:
                                    flow_amount_cell[
                                        7] = flow_amount_cell[
                                            7] + prop2
                                else:
                                    flow_amount_cell[7] = prop2
                                flow_amount_cell[6] = prop
                                state = 5
                            elif l == 4 and fldir[l] == 0:
                                flow_amount_cell[7] = flowcells

                            if l == 5 and 0 < fldir[l] < FB:
                                if state == 5:
                                    flow_amount_cell[
                                        6] = flow_amount_cell[
                                            6] + prop2
                                else:
                                    flow_amount_cell[6] = prop2
                                flow_amount_cell[5] = prop
                                state = 6
                            elif l == 5 and fldir[l] == 0:
                                flow_amount_cell[6] = flowcells

                            if l == 6 and 0 < fldir[l] < FB:
                                if state == 6:
                                    flow_amount_cell[
                                        5] = flow_amount_cell[
                                            5] + prop2
                                else:
                                    flow_amount_cell[5] = prop2
                                flow_amount_cell[3] = prop
                                state = 7
                            elif l == 6 and fldir[l] == 0:
                                flow_amount_cell[5] = flowcells

                            if l == 7 and 0 < fldir[l] < FB:
                                if state == 7:
                                    flow_amount_cell[
                                        3] = flow_amount_cell[
                                            3] + prop2
                                else:
                                    flow_amount_cell[3] = prop2
                                if state2 == 1:
                                    flow_amount_cell[
                                        0] = flow_amount_cell[
                                            0] + prop
                                else:
                                    flow_amount_cell[0] = prop
                            elif l == 7 and fldir[l] == 0:
                                flow_amount_cell[3] = flowcells

                    state = 0

                    if abs(sum(flprop) - 1.0) > 1e-5:
                        Logger.info(
                            f"Error - sum of flow proportions {sum(flprop)} in"
                            f"cell ({i}, {j}) is not equal to 1.0"
                        )
                    if abs(sum(flow_amount_cell) - 1.0) > 1e-5:
                        Logger.info(
                            f"Error - sum of flow amount "
                            f"{sum(flow_amount_cell)} in cell ({i}, {j}) is "
                            f"not equal to 1.0"
                        )

                    # same direction as in ArcGIS
                    flow_direction = np.array((
                        flow_amount_cell[4], flow_amount_cell[7],
                        flow_amount_cell[6], flow_amount_cell[5],
                        flow_amount_cell[3], flow_amount_cell[0],
                        flow_amount_cell[1], flow_amount_cell[2]
                    ))

                    # 1 where flow_direction > 0, 0 elsewhere
                    fldirr = (flow_direction > 0).astype('int8')

                    int_val = boolToInt(fldirr)
                    val_array2[i][j] = int_val

                    val_array[i][j] = flow_direction

                    # getting outfall maximum of flow direction amount from
                    # each cell to determine outfall for rill
                    ind = np.argmax(flow_direction)
                    if ind == 0:
                        fd_rill[i][j] = 1
                    if ind == 1:
                        fd_rill[i][j] = 2
                    if ind == 2:
                        fd_rill[i][j] = 4
                    if ind == 3:
                        fd_rill[i][j] = 8
                    if ind == 4:
                        fd_rill[i][j] = 16
                    if ind == 5:
                        fd_rill[i][j] = 32
                    if ind == 6:
                        fd_rill[i][j] = 64
                    if ind == 7:
                        fd_rill[i][j] = 128

                # case that in raster are places where more than one neighbor
                # has exact same height value so circulation is possible
                else:
                    if mat_fd[i][j] == 1:
                        val_array[i][j][0] = 1.0
                        val_array2[i][j] = 1
                        fd_rill[i][j] = 1
                    if mat_fd[i][j] == 2:
                        val_array[i][j][1] = 1.0
                        val_array2[i][j] = 2
                        fd_rill[i][j] = 2
                    if mat_fd[i][j] == 4:
                        val_array[i][j][2] = 1.0
                        val_array2[i][j] = 4
                        fd_rill[i][j] = 4
                    if mat_fd[i][j] == 8:
                        val_array[i][j][3] = 1.0
                        val_array2[i][j] = 8
                        fd_rill[i][j] = 8
                    if mat_fd[i][j] == 16:
                        val_array[i][j][4] = 1.0
                        val_array2[i][j] = 16
                        fd_rill[i][j] = 16
                    if mat_fd[i][j] == 32:
                        val_array[i][j][5] = 1.0
                        val_array2[i][j] = 32
                        fd_rill[i][j] = 32
                    if mat_fd[i][j] == 64:
                        val_array[i][j][6] = 1.0
                        val_array2[i][j] = 64
                        fd_rill[i][j] = 64
                    if mat_fd[i][j] == 128:
                        val_array[i][j][7] = 1.0
                        val_array2[i][j] = 128
                        fd_rill[i][j] = 128
    return val_array, fd_rill

# final rasters creation
