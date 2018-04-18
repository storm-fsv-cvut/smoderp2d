import math
import sys

class Size:
    @staticmethod
    def size(arrayNBytes, m=1.0):
        """Method to compute size of class arrays.    
        
        :param <numpy array>.nbytes arrayNBytes:
        :param float m: value in denominator to get bytes, kilobytes
        (m=2**10), megabytes (m=2**10+m**10) and so on.
        """
        # arrayNBytes eq self.state.nbytes
        return (self.n * arrayNBytes) / m

class Globals:
    """Gloobals contains global variables from data_preparation, in
    instance of class needed the data are taken from import of this
    class.
    """
    # area of a raster cell in meters
    pixel_area = None
    # number of rows in rasters
    r = None
    # number of columns in rasters
    c = None
    # id of rows in computational domain
    rr = None
    # id of columns in computational domain
    rc = None
    # id of rows in at the boundary of computational domain
    br = None
    # id of columns in at the boundary of computational domain
    bc = None
    # left bottom corner x coordinate of raster
    xllcorner = None
    # left bottom corner y coordinate of raster
    yllcorner = None
    # no data value for raster
    NoDataValue = None
    # no data integer value for raster
    NoDataInt = None
    # size of raster cell
    dx = None
    # size of raster cell
    dy = None
    # type of computation
    type_of_computing = None
    # path to a output directory
    outdir = None
    # raster with labeled boundary cells
    mat_boundary = None
    # list containing coordinates of catchment outlet cells
    outletCells = None
    # array containing information of hydrogram points
    array_points = None
    # combinatIndex
    combinatIndex = None
    # time step
    delta_t = None
    # raster contains potential interception data
    mat_pi = None
    # raster contains leaf area data
    mat_ppl = None
    # raster contains surface retention data
    surface_retention = None
    # raster contains id of infiltration type
    mat_inf_index = None
    # raster contains critical water level
    mat_hcrit = None
    # raster contains parameter of power law for surface runoff
    mat_aa = None
    # raster contains parameter of power law for surface runoff
    mat_b = None
    # raster contains surface retention data
    mat_reten = None
    # raster contains flow direction datas
    mat_fd = None
    # raster contains digital elevation model
    mat_dmt = None
    # raster contains efective couterline data
    mat_efect_vrst = None
    # raster contains surface slopes data
    mat_slope = None
    # raster labels not a number cells
    mat_nan = None
    # raster contains parameters ...
    mat_a = None
    # raster contains parameters ...
    mat_n = None
    # ???
    points = None
    # ???
    poradi = None
    # end time of computation
    end_time = None
    # ???
    spix = None
    # raster contains cell flow state information
    state_cell = None
    # path to directory for temporal data storage
    temp = None
    # ???
    vpix = None
    # bool variable for flow direction algorithm (false=one direction, true
    # multiple flow direction)
    mfda = None
    # list contains the precipitation data
    sr = None
    # counter of precipitation intervals
    itera = None
    # ???
    toky = None
    # ???
    cell_stream = None
    # raster contains the reach id data
    mat_tok_reach = None
    # ???
    STREAM_RATIO = None
    # ???
    tokyLoc = None
    # ???
    maxdt = None
    # ???
    extraOut = None
    
    def get_pixel_area(self):
        return self.pixel_area

    def get_rows(self):
        return self.r

    def get_cols(self):
        return self.c

    def get_rrows(self):
        return self.rr

    def get_rcols(self):
        return self.rc

    def get_bor_rows(self):
        return self.br

    def get_bor_cols(self):
        return self.bc

    def get_xllcorner(self):
        return self.xllcorner

    def get_yllcorner(self):
        return self.yllcorner

    def get_NoDataValue(self):
        return self.NoDataValue

    def get_NoDataInt(self):
        return self.NoDataInt

    def get_dx(self):
        return self.dx

    def get_dy(self):
        return self.dy

    def get_type_of_computing(self):
        return self.type_of_computing

    def get_outdir(self):
        return self.outdir

    def get_mat_boundary(self):
        return self.mat_boundary

    def get_outletCells(self):
        return self.outletCells

    def get_array_points(self):
        return self.array_points

    def get_combinatIndex(self):
        return self.combinatIndex

    def get_delta_t(self):
        return self.delta_t

    def get_mat_pi(self):
        return self.mat_pi

    def get_mat_ppl(self):
        return self.mat_ppl

    def get_surface_retention(self):
        return self.surface_retention

    def get_mat_inf_index(self):
        return self.mat_inf_index

    def get_mat_hcrit(self):
        return self._mat_hcrit

    def get_mat_aa(self):
        return self.mat_aa

    def get_mat_b(self):
        return self.mat_b

    def get_mat_reten(self):
        return self.mat_reten

    def get_mat_fd(self):
        return self.mat_fd

    def get_mat_dmt(self):
        return self.mat_dmt

    def get_mat_efect_vrst(self):
        return self.mat_efect_vrst

    def get_mat_slope(self, i, j):
        return self.mat_slope[i][j]

    def get_mat_nan(self):
        return self.mat_nan

    def get_mat_a(self):
        return self.mat_a

    def get_mat_n(self, i, j):
        return self.mat_n[i][j]

    def get_points(self):
        return self.points

    def get_poradi(self):
        return self.poradi

    def get_end_tim(self):
        return self.end_time

    def get_spix(self):
        return self.spix

    def get_state_cell(self):
        return self.state_cell

    def get_temp(self):
        return self.temp

    def get_vpix(self):
        return self.vpix

    def get_mfda(self):
        return self.mfda

    def get_sr(self):
        return self.sr

    def get_itera(self):
        return self.itera

    def get_toky(self):
        return self.toky

    def get_cell_stream(self):
        return self.cell_stream

    def get_mat_tok_reach(self, i, j):
        return self.mat_tok_reach[i][j]

    def get_STREAM_RATIO(self):
        return self.STREAM_RATIO

    def get_tokyLoc(self):
        return self.tokyLoc
