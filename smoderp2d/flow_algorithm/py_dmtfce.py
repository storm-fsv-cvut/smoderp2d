import numpy as np
import math


from smoderp2d.providers import Logger


FB = math.pi / 4  # facet boundary
PI_HALF = math.pi / 2
THREE_PI_HALF = 3 * math.pi / 2
VE = 4  # variable exponent

def neighbors(i, j, array, x, y):  # function to determine all neighbor cell to actual cell in the raster dataset
    """Return all neigbours to actuall cell 
    in the raster dataset
    """
    if i > 0 and i < (x - 1) and j > 0 and j < (y - 1):  # non edge cells
        nb1 = array[i - 1][j - 1]
        nb2 = array[i - 1][j]
        nb3 = array[i - 1][j + 1]
        nb4 = array[i][j - 1]
        nb5 = array[i][j + 1]
        nb6 = array[i + 1][j - 1]
        nb7 = array[i + 1][j]
        nb8 = array[i + 1][j + 1]

    elif i == 0 and j > 0 and j < (y - 1):  # upper edge
        nb1 = -1
        nb2 = -1
        nb3 = -1
        nb4 = array[i][j - 1]
        nb5 = array[i][j + 1]
        nb6 = array[i + 1][j - 1]
        nb7 = array[i + 1][j]
        nb8 = array[i + 1][j + 1]

    elif i > 0 and i < (x - 1) and j == 0:  # left edge
        nb1 = -1
        nb2 = array[i - 1][j]
        nb3 = array[i][j + 1]
        nb4 = -1
        nb5 = array[i][j + 1]
        nb6 = -1
        nb7 = array[i + 1][j]
        nb8 = array[i + 1][j + 1]

    elif i > 0 and i < (x - 1) and j == (y - 1):  # right edge
        nb1 = array[i - 1][j - 1]
        nb2 = array[i - 1][j]
        nb3 = -1
        nb4 = array[i][j - 1]
        nb5 = -1
        nb6 = array[i + 1][j - 1]
        nb7 = array[i + 1][j]
        nb8 = -1

    elif i == (x - 1) and j > 0 and j < (y - 1):  # lower edge
        nb1 = array[i - 1][j - 1]
        nb2 = array[i - 1][j]
        nb3 = array[i - 1][j + 1]
        nb4 = array[i][j - 1]
        nb5 = array[i][j + 1]
        nb6 = -1
        nb7 = -1
        nb8 = -1

    elif i == 0 and j == 0:  # upper left edge
        nb1 = -1
        nb2 = -1
        nb3 = -1
        nb4 = -1
        nb5 = array[i][j + 1]
        nb6 = -1
        nb7 = array[i + 1][j]
        nb8 = array[i + 1][j + 1]

    elif i == 0 and j == (y - 1):  # upper right edge
        nb1 = -1
        nb2 = -1
        nb3 = -1
        nb4 = array[i][j - 1]
        nb5 = -1
        nb6 = array[i + 1][j - 1]
        nb7 = array[i + 1][j]
        nb8 = -1

    elif i == (x - 1) and j == 0:  # lowed left edge
        nb1 = -1
        nb2 = array[i - 1][j]
        nb3 = array[i][j + 1]
        nb4 = -1
        nb5 = array[i][j + 1]
        nb6 = -1
        nb7 = -1
        nb8 = -1

    elif i == (x - 1) and j == (y - 1):  # lower right edge
        nb1 = array[i - 1][j - 1]
        nb2 = array[i - 1][j]
        nb3 = -1
        nb4 = array[i][j - 1]
        nb5 = -1
        nb6 = -1
        nb7 = -1
        nb8 = -1

    return nb1, nb2, nb3, nb4, nb5, nb6, nb7, nb8


def removeCellsWithSameHeightNeighborhood(mat_dmt, mat_nan, rows, cols):  # function determines if cell neighborhood has exactly same values of height a and than it save that cell as NoData
    "Returns an array with the values of heights, adjusted for the value of NoData cells"

    bad_cells = []

    # finding problem cells with same height neogborhood
    for i in range(rows):
        for j in range(cols):
            c = [i, j]
            count_nbrs = 0
            point_m = mat_dmt[i][j]

            if i > 0 and i < (rows - 1) and j > 0 and j < (cols - 1):  # non edge cells - edge cells are excluded thanks to slope trimming

                nbrs = [mat_dmt[i - 1][j - 1],
                        mat_dmt[i - 1][j],
                        mat_dmt[i - 1][j + 1],
                        mat_dmt[i][j - 1],
                        mat_dmt[i][j + 1],
                        mat_dmt[i + 1][j - 1],
                        mat_dmt[i + 1][j],
                        mat_dmt[i + 1][j + 1]]

                for k in range(8):
                    if point_m > 0 and point_m == nbrs[k]:
                        count_nbrs = count_nbrs + 1
                if count_nbrs >= 7:  # compare number of neighbours with the same height
                    bad_cells.append(c)
                    bc = 1

    Logger.info(
        "Possible water circulation! Check the input DTM raster for flat areas with the same height neighborhood."
    )
    # all problem cells set as NoData
    if len(bad_cells) > 0:
        for i in range(rows):
            for j in range(cols):
                if bc == 1:
                    bc_i = bad_cells[0][0]
                    bc_j = bad_cells[0][1]

                    if bc_i == i and bc_j == j:
                        mat_dmt[i][j] = -3.40282346639e+038
                        mat_nan[i][j] = -3.40282346639e+038
                        bad_cells.pop(0)
                        if len(bad_cells) == 0:
                            bc = 0
                else:
                    break

    return mat_dmt, mat_nan


def dirSlope(point_m, nbrs, vpix, spix):  
    """ function calculates for each triangular facet outflow direction and slope """
    "Return a list of direction a slope values for each triangular facet"
    direction = np.zeros(8)
    slope = np.zeros(8)
    VPIX_SQRT = vpix * math.sqrt(2)
    d0 = -1
    s0 = -1
    d1 = -1
    s1 = -1
    d2 = -1
    s2 = -1
    d3 = -1
    s3 = -1
    d4 = -1
    s4 = -1
    d5 = -1
    s5 = -1
    d6 = -1
    s6 = -1
    d7 = -1
    s7 = -1

    for k in range(8):
        # calculation for each triangular facet
        if k == 0:  # NW -N
            # NoData values or both neighbor points are with higher z-value
            if nbrs[0] < 0 and nbrs[1] < 0 or (nbrs[0] > point_m and nbrs[1] > point_m):
                d0 = -1
                s0 = -1
            # one of two neighbor points has NoData value
            elif nbrs[0] > 0 and nbrs[1] < 0:
                d0 = 0
                s0 = (point_m - nbrs[0]) / VPIX_SQRT
            # one of two neighbor points has NoData value
            elif nbrs[1] > 0 and nbrs[0] < 0 or (abs(point_m - nbrs[1]) < 1e-8 and nbrs[0] > point_m):
                d0 = FB
                s0 = (point_m - nbrs[1]) / vpix
            else:
                x1 = spix
                x2 = 0
                y1 = vpix
                y2 = vpix
                z1 = nbrs[0] - point_m
                z2 = nbrs[1] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d0 = 0
                elif nx == 0 and ny < 0:
                    d0 = math.pi
                elif nx > 0:
                    d0 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d0 = THREE_PI_HALF - math.atan2(ny, nx)
                s0 = math.sqrt(z1 * z1 / y1 / y1 / 2 + z2 / y2 * z2 / y2)

                if d0 > FB:
                    if point_m >= nbrs[1] and nbrs[0] >= nbrs[1]:
                        d0 = FB
                        s0 = (point_m - nbrs[1]) / vpix
                    elif point_m >= nbrs[0] and nbrs[1] >= nbrs[0]:
                        d0 = 0
                        s0 = (point_m - nbrs[0]) / VPIX_SQRT
                    else:
                        d0 = -1
                        s0 = -1

        elif k == 1:  # N - NE
            if nbrs[1] < 0 and nbrs[2] < 0 or (nbrs[1] > point_m and nbrs[2] > point_m):
                d1 = -1
                s1 = -1
            elif nbrs[1] > 0 and nbrs[2] < 0:
                d1 = 0
                s0 = (point_m - nbrs[1]) / vpix
            elif nbrs[2] > 0 and nbrs[1] < 0 or (abs(point_m - nbrs[2]) < 1e-8 and nbrs[1] > point_m):
                d1 = FB
                s0 = (point_m - nbrs[2]) / VPIX_SQRT
            else:
                x1 = 0
                x2 = spix
                y1 = vpix
                y2 = vpix
                z1 = nbrs[1] - point_m
                z2 = nbrs[2] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d1 = 0
                elif nx == 0 and ny < 0:
                    d1 = math.pi
                elif nx > 0:
                    d1 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d1 = THREE_PI_HALF - math.atan2(ny, nx)
                s1 = math.sqrt(z1 / y1 * z1 / y1 + z2 / x2 * z2 / x2)

                if d1 > FB:
                    if point_m >= nbrs[2] and nbrs[1] >= nbrs[2]:
                        d1 = FB
                        s1 = (point_m - nbrs[2]) / VPIX_SQRT
                    elif point_m >= nbrs[1] and nbrs[2] >= nbrs[1]:
                        d1 = 0
                        s1 = (point_m - nbrs[1]) / vpix
                    else:
                        d1 = -1
                        s1 = -1

        elif k == 2:  # NE - E
            if nbrs[2] < 0 and nbrs[4] < 0 or (nbrs[2] > point_m and nbrs[4] > point_m):
                d2 = -1
                s2 = -1
            elif nbrs[2] > 0 and nbrs[4] < 0:
                d2 = 0
                s2 = (point_m - nbrs[2]) / VPIX_SQRT
            elif nbrs[4] > 0 and nbrs[2] < 0 or (abs(point_m - nbrs[4]) < 1e-8 and nbrs[2] > point_m):
                d2 = FB
                s2 = (point_m - nbrs[4]) / spix
            else:
                x1 = spix
                x2 = spix
                y1 = vpix
                y2 = 0
                z1 = nbrs[2] - point_m
                z2 = nbrs[4] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d2 = 0
                elif nx == 0 and ny < 0:
                    d2 = math.pi
                elif nx > 0:
                    d2 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d2 = THREE_PI_HALF - math.atan2(ny, nx)
                s2 = math.sqrt(z1 * z1 / y1 / y1 / 2 + z2 / y1 * z2 / y1)

                if d2 > FB:
                    if point_m >= nbrs[4] and nbrs[2] >= nbrs[4]:
                        d2 = FB
                        s2 = (point_m - nbrs[4]) / spix

                    elif point_m >= nbrs[2] and nbrs[4] >= nbrs[2]:
                        d2 = 0
                        s2 = (point_m - nbrs[2]) / VPIX_SQRT
                    else:
                        d2 = -1
                        s2 = -1

        elif k == 3:  # E - SE
            if nbrs[4] < 0 and nbrs[7] < 0 or (nbrs[4] > point_m and nbrs[7] > point_m):
                d3 = -1
                s3 = -1
            elif nbrs[4] > 0 and nbrs[7] < 0:
                d3 = 0
                s3 = (point_m - nbrs[4]) / spix
            elif nbrs[7] > 0 and nbrs[4] < 0 or (abs(point_m - nbrs[7]) < 1e-8 and nbrs[4] > point_m):
                d3 = FB
                s3 = (point_m - nbrs[7]) / VPIX_SQRT
            else:
                x1 = spix
                x2 = spix
                y1 = 0
                y2 = vpix
                z1 = nbrs[4] - point_m
                z2 = nbrs[7] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d3 = 0
                elif nx == 0 and ny < 0:
                    d3 = math.pi
                elif nx > 0:
                    d3 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d3 = THREE_PI_HALF - math.atan2(ny, nx)
                s3 = math.sqrt(z1 / x1 * z1 / x1 + z2 / y2 * z2 / y2)

                if d3 > FB:
                    if point_m >= nbrs[7] and nbrs[4] >= nbrs[7]:
                        d3 = FB
                        s3 = (point_m - nbrs[7]) / VPIX_SQRT
                    elif point_m >= nbrs[4] and nbrs[7] >= nbrs[4]:
                        d3 = 0
                        s3 = (point_m - nbrs[4]) / spix
                    else:
                        d3 = -1
                        s3 = -1

        elif k == 4:  # SE - S
            if nbrs[7] < 0 and nbrs[6] < 0 or (nbrs[7] > point_m and nbrs[6] > point_m):
                d4 = -1
                s4 = -1
            elif nbrs[7] > 0 and nbrs[6] < 0:
                d4 = 0
                s4 = (point_m - nbrs[7]) / VPIX_SQRT
            elif nbrs[6] > 0 and nbrs[7] < 0 or (abs(point_m - nbrs[6]) < 1e-8 and nbrs[7] > point_m):
                d4 = FB
                s4 = (point_m - nbrs[6]) / vpix
            else:
                x1 = spix
                x2 = 0
                y1 = vpix
                y2 = vpix
                z1 = nbrs[7] - point_m
                z2 = nbrs[6] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d4 = 0
                elif nx == 0 and ny < 0:
                    d4 = math.pi
                elif nx > 0:
                    d4 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d4 = THREE_PI_HALF - math.atan2(ny, nx)
                s4 = math.sqrt(z1 * z1 / y1 / y1 / 2 + z2 / x1 * z2 / x1)

                if d4 > FB:
                    if point_m >= nbrs[6] and nbrs[7] >= nbrs[6]:
                        d4 = FB
                        s4 = (point_m - nbrs[6]) / vpix
                    elif point_m >= nbrs[7] and nbrs[6] >= nbrs[7]:
                        d4 = 0
                        s4 = (point_m - nbrs[7]) / VPIX_SQRT
                    else:
                        d4 = -1
                        s4 = -1

        elif k == 5:  # S - SW
            if nbrs[6] < 0 and nbrs[5] < 0 or (nbrs[6] > point_m and nbrs[5] > point_m):
                d5 = -1
                s5 = -1
            elif nbrs[6] > 0 and nbrs[5] < 0:
                d5 = 0
                s5 = (point_m - nbrs[6]) / vpix
            elif nbrs[5] > 0 and nbrs[6] < 0 or (abs(point_m - nbrs[5]) < 1e-8 and nbrs[6] > point_m):
                d5 = FB
                s5 = (point_m - nbrs[5]) / VPIX_SQRT
            else:
                x1 = 0
                x2 = spix
                y1 = vpix
                y2 = vpix
                z1 = nbrs[6] - point_m
                z2 = nbrs[5] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d5 = 0
                elif nx == 0 and ny < 0:
                    d5 = math.pi
                elif nx > 0:
                    d5 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d5 = THREE_PI_HALF - math.atan2(ny, nx)
                s5 = math.sqrt(z1 / y1 * z1 / y1 + z2 / x2 * z2 / x2)

                if d5 > FB:
                    if point_m >= nbrs[5] and nbrs[6] >= nbrs[5]:
                        d5 = FB
                        s5 = (point_m - nbrs[5]) / VPIX_SQRT
                    elif point_m >= nbrs[6] and nbrs[5] >= nbrs[6]:
                        d5 = 0
                        s5 = (point_m - nbrs[6]) / vpix
                    else:
                        d5 = -1
                        s5 = -1

        elif k == 6:  # SW - W
            if nbrs[5] < 0 and nbrs[3] < 0 or (nbrs[5] > point_m and nbrs[3] > point_m):
                d6 = -1
                s6 = -1
            elif nbrs[5] > 0 and nbrs[3] < 0:
                d6 = 0
                s6 = (point_m - nbrs[5]) / VPIX_SQRT
            elif nbrs[3] > 0 and nbrs[5] < 0 or (abs(point_m - nbrs[3]) < 1e-8 and nbrs[5] > point_m):
                d6 = FB
                s6 = (point_m - nbrs[3]) / spix
            else:
                x1 = spix
                x2 = spix
                y1 = vpix
                y2 = 0
                z1 = nbrs[5] - point_m
                z2 = nbrs[3] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d6 = 0
                elif nx == 0 and ny < 0:
                    d6 = math.pi
                elif nx > 0:
                    d6 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d6 = THREE_PI_HALF - math.atan2(ny, nx)
                s6 = math.sqrt(z1 * z1 / y1 / y1 / 2 + z2 / y1 * z2 / y1)

                if d6 > FB:
                    if point_m >= nbrs[3] and nbrs[5] >= nbrs[3]:
                        d6 = FB
                        s6 = (point_m - nbrs[3]) / spix
                    elif point_m >= nbrs[5] and nbrs[3] >= nbrs[5]:
                        d6 = 0
                        s6 = (point_m - nbrs[5]) / VPIX_SQRT
                    else:
                        d6 = -1
                        s6 = -1

        elif k == 7:  # W - NW
            if nbrs[3] < 0 and nbrs[0] < 0 or (nbrs[3] > point_m and nbrs[0] > point_m):
                d7 = -1
                s7 = -1
            elif nbrs[3] > 0 and nbrs[0] < 0:
                d7 = 0
                s7 = (point_m - nbrs[3]) / spix
            elif nbrs[0] > 0 and nbrs[3] < 0 or (abs(point_m - nbrs[0]) < 1e-8 and nbrs[3] > point_m):
                d7 = FB
                s7 = (point_m - nbrs[0]) / VPIX_SQRT
            else:
                x1 = spix
                x2 = spix
                y1 = 0
                y2 = vpix
                z1 = nbrs[3] - point_m
                z2 = nbrs[0] - point_m

                # the normal vector
                nx = z1 * y2 - z2 * y1
                ny = z1 * x2 - x1 * z2
                # the direction d and slope s
                if nx == 0 and ny >= 0:
                    d7 = 0
                elif nx == 0 and ny < 0:
                    d7 = math.pi
                elif nx > 0:
                    d7 = PI_HALF - math.atan2(ny, nx)
                elif nx < 0:
                    d7 = THREE_PI_HALF - math.atan2(ny, nx)
                s7 = math.sqrt(z1 / x1 * z1 / x1 + z2 / y2 * z2 / y2)

                if d7 > FB:
                    if point_m >= nbrs[0] and nbrs[3] >= nbrs[0]:
                        d7 = FB
                        s7 = (point_m - nbrs[0]) / VPIX_SQRT
                    elif point_m >= nbrs[3] and nbrs[0] >= nbrs[3]:
                        d7 = 0
                        s7 = (point_m - nbrs[3]) / spix
                    else:
                        d7 = -1
                        s7 = -1

    if (d7 == FB and d0 == 0) or (d0 > 0 and d0 < FB):
        direction[0] = d0
        slope[0] = s0
    else:
        direction[0] = -1
        slope[0] = -1

    if (d0 == FB and d1 == 0) or (d1 > 0 and d1 < FB):
        direction[1] = d1
        slope[1] = s1
    else:
        direction[1] = -1
        slope[1] = -1

    if (d1 == FB and d2 == 0) or (d2 > 0 and d2 < FB):
        direction[2] = d2
        slope[2] = s2
    else:
        direction[2] = -1
        slope[2] = -1

    if (d2 == FB and d3 == 0) or (d3 > 0 and d3 < FB):
        direction[3] = d3
        slope[3] = s3
    else:
        direction[3] = -1
        slope[3] = -1

    if (d3 == FB and d4 == 0) or (d4 > 0 and d4 < FB):
        direction[4] = d4
        slope[4] = s4
    else:
        direction[4] = -1
        slope[4] = -1

    if (d4 == FB and d5 == 0) or (d5 > 0 and d5 < FB):
        direction[5] = d5
        slope[5] = s5
    else:
        direction[5] = -1
        slope[5] = -1

    if (d5 == FB and d6 == 0) or (d6 > 0 and d6 < FB):
        direction[6] = d6
        slope[6] = s6
    else:
        direction[6] = -1
        slope[6] = -1

    if (d6 == FB and d7 == 0) or (d7 > 0 and d7 < FB):
        direction[7] = d7
        slope[7] = s7
    else:
        direction[7] = -1
        slope[7] = -1

    return direction, slope


def boolToInt(x):  # function creates bit value from vector of ones and zeros
    "Return int value"
    y = 0
    for i, j in enumerate(x):
        if j:
            y += 1 << i
    return y


def lenght(flow_direction, vpix, spix):
    if fd == 32 or fd == 128 or fd == 8 or fd == 2:
        L = math.sqrt(vpix * vpix + spix * spix)
    elif fd == 64 or fd == 4:
        L = vpix
    elif fd == 1 or fd == 16:
        L = spix
    return L
