import numpy as np
import numpy.ma as ma

from smoderp2d.core.general import GridGlobals


# defines inflows to the cell of raster based on the flow direction raster
#
#  @inflows return list defines relative position of cells \f$ i+m \f$ and
#  \f$ j+n \f$ from which the water flows to cell \f$ i,j \f$. \n
#
#  According to the figure, the inflows list at the cell \f$ i,j \f$ looks as
#  follows:\n
#
#  \f$ m_1 = inflows[i][j][0][0] = -1  \f$ \n
#  \f$ n_1 = inflows[i][j][0][1] =  0  \f$ \n
#  \f$ m_2 = inflows[i][j][1][0] =  -1 \f$ \n
#  \f$ n_2 = inflows[i][j][1][1] =  +1 \f$ \n
#
# \image html inflows.png "meaning of #inflows list elements" width=2cm
#
def new_inflows(mat_fd):
    """TODO.

    :param mat_fd: flow direction
    """
    direction = [128, 64, 32, 16, 8, 4, 2, 1]

    r = mat_fd.shape[0]
    c = mat_fd.shape[1]

    in_fldir = ma.masked_array(np.zeros([r, c], int), mask=GridGlobals.masks)

    inflows = []

    for i in range(r):
        inflows.append([])

        for j in range(c):
            inflows[i].append(__directionsInflow(mat_fd, i, j))

    return inflows


def __directionsInflow(mat_fd, i, j):
    """Compute inflows.

    numpy (axis 0 - rows, axis 1 - cols):
    | -1 -1 | -1  0 | -1  1 |
    |  0 -1 |  0  0 |  0  1 |
    |  1 -1 |  1  0 |  1  1 |

    :param mat_fd: flow direction (array)
    :param i: numpy axis-0 index
    :param j: numpy axis-1 index

    :return list: inflows (eg. [[-1, 0], [-1, 1]] inflow from north and north-east)
    """
    inflow_directions = [[-1, 1, 8], [-1, 0, 4], [-1, -1, 2], [0, -1, 1],
            [1, -1, 128], [1, 0, 64], [1, 1, 32], [0, 1, 16]]
    inflows = []

    for k in range(len(inflow_directions)):
        a = i + inflow_directions[k][0]
        b = j + inflow_directions[k][1]
        try:
            value = mat_fd[a][b]
        except IndexError:
            value = -1
        if value == inflow_directions[k][2]:
            inflows.append([inflow_directions[k][0], inflow_directions[k][1]])

    return inflows


def __directions(inflow, direction):
    """TODO.

    :param inflow: TODO
    :param direction: TODO
    """
    y = 0
    co = [[1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1]]
    cellin = []
    for z in direction:
        if inflow >= z:
            cellin.append(co[y])
            inflow = inflow - direction[y]
            y += 1
        else:
            y += 1

    return cellin

def inflow_dir(mat_fd, i, j):
    inflow_dirs = np.zeros(8, float)
    
    # inflow matrix stores the information about the inflow directions (0 if there is no inflow, 1 if there is inflow from the direction) 
    # 32  64  128
    # 16      1
    # 8   4   2
    

    coco = [[-1, 1, 8], [-1, 0, 4], [-1, -1, 2], [0, -1, 1],
            [1, -1, 128], [1, 0, 64], [1, 1, 32], [0, 1, 16]]
    pocet = len(coco)
    for k in range(pocet):
        a = i + coco[k][0]
        b = j + coco[k][1]
        if a < 0 or b < 0:
                value = -1
        else:        
            try:
                value = mat_fd[a][b]
            except IndexError:
                value = -1        
        
        if value == coco[k][2]:
            inflow_dirs[k] = 1.0   
    return inflow_dirs
