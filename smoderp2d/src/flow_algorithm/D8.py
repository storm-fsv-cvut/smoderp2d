import numpy as np


# defines inflows to the cell of raster based on the flow direction raster
#
#  @infloes return list defines relative postion of cells \f$ i+m \f$ and \f$ j+n \f$ from which
#  the water flows to cell \f$ i,j \f$. \n
#
#  Accordinto the figure, the inflows list at the cell \f$ i,j \f$ looks as follows:\n
#
#  \f$ m_1 = inflows[i][j][0][0] = -1  \f$ \n
#  \f$ n_1 = inflows[i][j][0][1] =  0  \f$ \n
#  \f$ m_2 = inflows[i][j][1][0] =  -1 \f$ \n
#  \f$ n_2 = inflows[i][j][1][1] =  +1 \f$ \n
#
# \image html inflows.png "meaning of #inflows list elements" width=2cm
#
def new_inflows(mat_fd):
    smer = [128, 64, 32, 16, 8, 4, 2, 1]

    r = mat_fd.shape[0]
    c = mat_fd.shape[1]

    in_fldir = np.zeros([r, c], int)

    inflows = []  # np.zeros(mat_a[r,c],float)

    for i in range(r):
        inflows.append([])

    for i in range(r):
        for j in range(c):
            inflows[i].append([])

    for i in range(r):
        for j in range(c):
            in_dir = __smeryInflow(mat_fd, i, j)
            in_fldir[i][j] = in_dir
            intok = __smery(in_dir, i, j, smer)
            inflows[i][j] = intok

    # for item in inflows :
        # print item
        # for item2 in item :
            # print item2
    # raw_input()
    return inflows


def __smeryInflow(mat_fd, i, j):
    coco = [[-1, 1, 8], [-1, 0, 4], [-1, -1, 2], [0, -1, 1],
            [1, -1, 128], [1, 0, 64], [1, 1, 32], [0, 1, 16]]
    pritok = 0
    pocet = len(coco)
    for k in range(pocet):
        a = i + coco[k][0]
        b = j + coco[k][1]
        try:
            value = mat_fd[a][b]
        except:
            value = -1
        if value == coco[k][2]:
            pritok = pritok + value
    return pritok


def __smery(inflow, i, j, smer):
    y = 0
    co = [[1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1]]
    cellin = []
    for z in smer:
        if inflow >= z:
            cellin.append(co[y])
            inflow = inflow - smer[y]
            y = y + 1
        else:
            y = y + 1
    y = 0
    return cellin
