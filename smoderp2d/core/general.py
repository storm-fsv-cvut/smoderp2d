import numpy as np

from smoderp2d.exceptions import SmoderpError

class Size(object):
    @staticmethod
    def size(arrayNBytes, m=1.0):
        """Method to compute size of class arrays.    
        
        :param <numpy array>.nbytes arrayNBytes:
        :param float m: value in denominator to get bytes, kilobytes
        (m=2**10), megabytes (m=2**10+m**10) and so on.
        """
        # arrayNBytes eq self.state.nbytes
        return (self.n * arrayNBytes) / m

class GridGlobals(object):
    # number of raster rows (int)
    r = None
    # number of raster columns (int)
    c = None
    # area of a raster cell in meters (float)
    pixel_area = None
    # id of rows in computational domain (list)
    rr = None
    # id of columns in computational domain (list of lists)
    # row out of computational domain is empty list
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

    def __init__(self):
        if self.r is None or self.c is None:
            raise SmoderpError("Global variables are not assigned")

        self.arr = np.empty((self.r, self.c), dtype=object)

    @classmethod        
    def get_dim(cls):
        return (cls.r, cls.c)

    @classmethod
    def get_pixel_area(cls):
        return cls.pixel_area

    @classmethod
    def get_region_dim(cls):
        return (cls.rr, cls.rc)

    @classmethod
    def get_border_dim(cls):
        return (cls.br, cls.bc)

    @classmethod
    def get_llcorner(cls):
        return (cls.xllcorner, cls.yllcorner)

    @classmethod
    def get_size(cls):
        return (cls.dx, cls.dy)

    @classmethod
    def get_no_data(cls):
        # TODO: int?
        return cls.NoDataValue

class DataGlobals:
    # raster contains leaf area data
    mat_ppl = None

    @classmethod
    def get_mat_ppl(cls, i, j):
        return cls.mat_ppl[i][j]
    
class Globals:
    """Globals contains global variables from data_preparation, in
    instance of class needed the data are taken from import of this
    class.
    """
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
    toky_loc = None
    # ???
    maxdt = None
    # ???
    extraOut = None
    # infiltration_type
    infiltration_type = None
    

    @classmethod
    def get_type_of_computing(cls):
        return cls.type_of_computing

    @classmethod
    def get_outdir(cls):
        return cls.outdir

    @classmethod
    def get_mat_boundary(cls):
        return cls.mat_boundary

    @classmethod
    def get_outletCells(cls):
        return cls.outletCells

    @classmethod
    def get_array_points(cls):
        return cls.array_points

    @classmethod
    def get_combinatIndex(cls):
        return cls.combinatIndex

    @classmethod
    def get_delta_t(cls):
        return cls.delta_t

    @classmethod
    def get_mat_pi(cls):
        return cls.mat_pi


    @classmethod
    def get_surface_retention(cls):
        return cls.surface_retention

    @classmethod
    def get_mat_inf_index(cls, i, j):
        return cls.mat_inf_index[i][j]

    @classmethod
    def get_mat_hcrit(cls, i, j):
        return cls.mat_hcrit[i][j]

    @classmethod
    def get_mat_aa(cls, i, j):
        return cls.mat_aa[i][j]

    @classmethod
    def get_mat_b(cls, i, j):
        return cls.mat_b[i][j]

    @classmethod
    def get_mat_reten(cls, i, j):
        return cls.mat_reten[i][j]

    @classmethod
    def get_mat_fd(cls):
        return cls.mat_fd

    @classmethod
    def get_mat_dmt(cls):
        return cls.mat_dmt

    @classmethod
    def get_mat_efect_vrst(cls):
        return cls.mat_efect_vrst

    @classmethod
    def get_mat_slope(cls, i, j):
        return cls.mat_slope[i][j]

    @classmethod
    def get_mat_nan(cls):
        return cls.mat_nan

    @classmethod
    def get_mat_a(cls):
        return cls.mat_a

    @classmethod
    def get_mat_n(cls, i, j):
        return cls.mat_n[i][j]

    @classmethod
    def get_points(cls):
        return cls.points

    @classmethod
    def get_poradi(cls):
        return cls.poradi

    @classmethod
    def get_end_tim(cls):
        return cls.end_time

    @classmethod
    def get_spix(cls):
        return cls.spix

    @classmethod
    def get_state_cell(cls):
        return cls.state_cell

    @classmethod
    def get_temp(cls):
        return cls.temp

    @classmethod
    def get_vpix(cls):
        return cls.vpix

    @classmethod
    def get_mfda(cls):
        return cls.mfda

    @classmethod
    def get_sr(cls):
        return cls.sr

    @classmethod
    def get_itera(cls):
        return cls.itera

    @classmethod
    def get_toky(cls):
        return cls.toky

    @classmethod
    def get_cell_stream(cls):
        return cls.cell_stream

    @classmethod
    def get_mat_tok_reach(cls, i, j):
        return cls.mat_tok_reach[i][j]

    @classmethod
    def get_STREAM_RATIO(cls):
        return cls.STREAM_RATIO

    @classmethod
    def get_toky_loc(cls):
        return cls.toky_loc
    
    @classmethod
    def get_infiltration_type(cls):
        #TODO 1 stands for philips infiltration
        #     the philips infiltration is the only implemented now
        return cls.infiltration_type
