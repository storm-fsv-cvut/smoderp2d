import numpy as np
import math


def flow_direction(dem, rr, rc, br, bc, pixel_size):

    dist = [math.sqrt(pixel_size),
            math.sqrt(pixel_size * pixel_size)]

    fd = np.zeros(dem.shape, int)

    n = fd.shape

    drop = np.zeros([8], float)
    # drop[0]  drop[3]  drop[5]
    # drop[1]           drop[6]
    # drop[2]  drop[4]  drop[7]

    dir_ = [32, 16, 8, 64, 4, 128, 1, 2]
    # 32  64  128
    # 16      1
    # 8   4   2

    for i in rr:
        for j in rc[i]:
            drop[0] = (dem[i][j] - dem[i - 1][j - 1]) / dist[0] * 100.00
            drop[1] = (dem[i][j] - dem[i][j - 1]) / dist[1] * 100.00
            drop[2] = (dem[i][j] - dem[i + 1][j - 1]) / dist[0] * 100.00
            drop[3] = (dem[i][j] - dem[i - 1][j]) / dist[1] * 100.00
            drop[4] = (dem[i][j] - dem[i + 1][j]) / dist[1] * 100.00
            drop[5] = (dem[i][j] - dem[i - 1][j + 1]) / dist[0] * 100.00
            drop[6] = (dem[i][j] - dem[i][j + 1]) / dist[1] * 100.00
            drop[7] = (dem[i][j] - dem[i + 1][j + 1]) / dist[0] * 100.00
            min_drop = np.argmax(drop)
            fd[i][j] = dir_[min_drop]

    for i in br:
        for j in bc[i]:

            if (i >= 1 and j >= 1):
                try:
                    drop[0] = (
                        dem[i][j] - dem[i - 1][j - 1]) / dist[0] * 100.00
                except:
                    drop[0] = -99999.0
            else:
                drop[0] = -99999.0

            if (j >= 1):
                try:
                    drop[1] = (dem[i][j] - dem[i][j - 1]) / dist[1] * 100.00
                except:
                    drop[1] = -99999.0
            else:
                drop[1] = -99999.0

            if (j >= 1):
                try:
                    drop[2] = (dem[i][j] - dem[i + 1][j - 1]) / dist[
                        0] * 100.00
                except:
                    drop[2] = -99999.0
            else:
                drop[2] = -99999.0

            if (i >= 1):
                try:
                    drop[3] = (dem[i][j] - dem[i - 1][j]) / dist[1] * 100.00
                except:
                    drop[3] = -99999.0
            else:
                drop[3] = -99999.0

            try:
                drop[4] = (dem[i][j] - dem[i + 1][j]) / dist[1] * 100.00
            except:
                drop[4] = -99999.0

            if (i >= 1):
                try:
                    drop[5] = (dem[i][j] - dem[i - 1][j + 1]) / dist[
                        0] * 100.00
                except:
                    drop[5] = -99999.0
            else:
                drop[5] = -99999.0

            try:
                drop[6] = (dem[i][j] - dem[i][j + 1]) / dist[1] * 100.00
            except:
                drop[6] = -99999.0

            try:
                drop[7] = (dem[i][j] - dem[i + 1][j + 1]) / dist[0] * 100.00
            except:
                drop[7] = -99999.0

            min_drop = np.argmax(drop)
            if (np.amax(drop) < 0.0):
                if (i == 0 and j == 0):
                    fd[i][j] = 32
                elif (i == 0 and j == n[1] - 1):
                    fd[i][j] = 8
                elif (i == n[0] - 1 and j == 0):
                    fd[i][j] = 128
                elif (i == n[0] - 1 and j == n[1] - 1):
                    fd[i][j] = 2
                else:
                    if (i == 0):
                        fd[i][j] = 64
                    elif (j == n[1] - 1):
                        fd[i][j] = 1
                    elif (i == n[0] - 1):
                        fd[i][j] = 4
                    elif (j == 0):
                        fd[i][j] = 16
                    else:
                        fd[i][j] = dir_[min_drop]
            else:
                fd[i][j] = dir_[min_drop]

    return fd
