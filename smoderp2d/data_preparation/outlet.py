# Class to find out the possible catchment outlets (Is not used anywhere?)
class Outlet:
    # constructor
    def __init__(self):

        # cells in the domain
        self.cell = []

        self.cellNeighbour = []
        self.outletCells = []

    # Function to determine cells indexes and neighbor of all cells in the domain
    def push(self, cellI, cellJ, mat_nan, noDataVal):
        cn = []
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (cellI + i or cellJ + j) < 0:
                    pass
                else:
                    if i != 0 or j != 0:
                        try:
                            val = mat_nan[cellI + i][cellJ + j]
                            if val > -1:
                                cn.append([cellI + i, cellJ + j])
                        except:
                            pass
        self.cell.append([cellI, cellJ])
        self.cellNeighbour.append(cn)

    # Determine which of cells in the domain are outlet. Outlet cell is the lowers cell compared to all its neighbors
    def find_outlets(self, dem):
        for i in range(len(self.cell)):
            lowest = True
            demCell = dem[self.cell[i][0]][self.cell[i][1]]
            cn = self.cellNeighbour[i]
            for k in range(len(cn)):
                if dem[cn[k][0]][cn[k][1]] < demCell:
                    lowest = False
            if lowest:
                self.outletCells.append(self.cell[i])
