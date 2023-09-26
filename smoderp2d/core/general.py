import numpy as np

from smoderp2d.exceptions import SmoderpError

class GridGlobalsArray(np.ndarray):
    """Class overriding np.ndarray to handle SMODERP border problems."""

    def get_item(self, item):
        """Get item at position.

        Return empty SurArrs when querying for values at negative positions,
        do normal query with __getitem__() otherwise.

        :param item: position in the array
        :return: object at position specified with item or empty SurArrs
        """
        if isinstance(item, list):
            item = tuple(item)

        if isinstance(item, tuple) and self.ndim > 1:
            if any(i < 0 for i in item if isinstance(i, int)):
                return self.invalid_sur_arr
        elif isinstance(item, int) or isinstance(item, float):
            if self.ndim > 1 and item < 0:
                return self.invalid_sur_arr

        return self[item]

    def set_outsides(self, surarrs):
        """Setup the empty SurArrs.

        The empty SurArrs is intended to be returned when querying values at
        negative positions.

        :param surarrs: SurrArs class
        """
        self.invalid_sur_arr = surarrs(0, 0, 0, 0, 0)


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
    NoDataValue = -9999
    # no data integer value for raster
    NoDataInt = None
    # size of raster cell
    dx = None
    # size of raster cell
    dy = None
    # masks
    masks = None

    def __init__(self):
        if self.r is None or self.c is None:
            raise SmoderpError("Global variables are not assigned")

        self.arr = GridGlobalsArray((self.r, self.c), dtype=object)

    @classmethod
    def get_dim(cls):
        return (cls.r, cls.c)

    @classmethod
    def get_pixel_area(cls):
        return cls.pixel_area

    @classmethod
    def set_pixel_area(cls, pa):
        cls.pixel_area = pa

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
    def set_llcorner(cls, xy):
        cls.xllcorner = xy[0]
        cls.yllcorner = xy[1]

    @classmethod
    def get_size(cls):
        return (cls.dx, cls.dy)

    @classmethod
    def set_size(cls, dxdy):
        cls.dx = dxdy[0]
        cls.dy = dxdy[1]
        cls.pixel_area = cls.dx * cls.dy

    @classmethod
    def get_no_data(cls):
        # TODO: int?
        return cls.NoDataValue

    @classmethod
    def reset(cls):
        """Reset static variables to their default values."""

        # number of raster rows (int)
        cls.r = None
        # number of raster columns (int)
        cls.c = None
        # area of a raster cell in meters (float)
        cls.pixel_area = None
        # id of rows in computational domain (list)
        cls.rr = None
        # id of columns in computational domain (list of lists)
        # row out of computational domain is empty list
        cls.rc = None
        # id of rows in at the boundary of computational domain
        cls.br = None
        # id of columns in at the boundary of computational domain
        cls.bc = None
        # left bottom corner x coordinate of raster
        cls.xllcorner = None
        # left bottom corner y coordinate of raster
        cls.yllcorner = None
        # no data value for raster
        cls.NoDataValue = -9999
        # no data integer value for raster
        cls.NoDataInt = None
        # size of raster cell
        cls.dx = None
        # size of raster cell
        cls.dy = None
        # masks
        cls.masks = None

class DataGlobals:
    # raster contains leaf area data
    mat_ppl = None

    @classmethod
    def get_mat_ppl(cls):
        return cls.mat_ppl

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
    # array containing information of hydrograph points
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
    mat_dem = None
    # raster contains efective couterline data
    mat_efect_cont = None
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
    # end time of computation
    end_time = None
    # raster contains cell flow state information
    state_cell = None
    # bool variable for flow direction algorithm (false=one direction, true
    # multiple flow direction)
    mfda = None
    # list contains the precipitation data
    sr = None
    # counter of precipitation intervals
    itera = None
    # ???
    streams = None
    # ???
    cell_stream = None
    # raster contains the reach id data
    mat_stream_reach = None
    # ???
    STREAM_RATIO = None
    # maximum allowed time step during compuation
    maxdt = None
    # if true extra data are stores in the point*.dat files
    extraOut = None
    # stream magic number
    streams_flow_inc = 1000
    # no segment downside
    streamsNextDownIdNoSegment = -1
    # slope width
    slope_width = None

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
    def get_mat_inf_index(cls):
        return cls.mat_inf_index

    @classmethod
    def get_mat_hcrit(cls):
        return cls.mat_hcrit

    @classmethod
    def get_mat_aa(cls):
        return cls.mat_aa

    @classmethod
    def get_mat_b(cls):
        return cls.mat_b

    @classmethod
    def get_mat_reten(cls):
        return cls.mat_reten

    @classmethod
    def get_mat_fd(cls):
        return cls.mat_fd

    @classmethod
    def get_mat_dem(cls):
        return cls.mat_dem

    @classmethod
    def get_mat_efect_cont(cls):
        return cls.mat_efect_cont

    @classmethod
    def get_mat_slope(cls):
        return cls.mat_slope

    @classmethod
    def get_mat_nan(cls):
        return cls.mat_nan

    @classmethod
    def get_mat_a(cls):
        return cls.mat_a

    @classmethod
    def get_mat_n(cls):
        return cls.mat_n

    @classmethod
    def get_points(cls):
        return cls.points

    @classmethod
    def get_end_tim(cls):
        return cls.end_time

    @classmethod
    def get_state_cell(cls):
        return cls.state_cell

    @classmethod
    def get_temp(cls):
        return cls.temp

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
    def get_streams(cls):
        return cls.streams

    @classmethod
    def get_cell_stream(cls):
        return cls.cell_stream

    @classmethod
    def get_mat_stream_reach(cls, i, j):
        return cls.mat_stream_reach[i][j]

    @classmethod
    def get_STREAM_RATIO(cls):
        return cls.STREAM_RATIO

    @classmethod
    def reset(cls):
        """Reset static variables to their default values."""
        # type of computation
        cls.type_of_computing = None
        # path to a output directory
        cls.outdir = None
        # raster with labeled boundary cells
        cls.mat_boundary = None
        # list containing coordinates of catchment outlet cells
        cls.outletCells = None
        # array containing information of hydrograph points
        cls.array_points = None
        # combinatIndex
        cls.combinatIndex = None
        # time step
        cls.delta_t = None
        # raster contains potential interception data
        cls.mat_pi = None
        # raster contains surface retention data
        cls.surface_retention = None
        # raster contains id of infiltration type
        cls.mat_inf_index = None
        # raster contains critical water level
        cls.mat_hcrit = None
        # raster contains parameter of power law for surface runoff
        cls.mat_aa = None
        # raster contains parameter of power law for surface runoff
        cls.mat_b = None
        # raster contains surface retention data
        cls.mat_reten = None
        # raster contains flow direction datas
        cls.mat_fd = None
        # raster contains digital elevation model
        cls.mat_dem = None
        # raster contains efective couterline data
        cls.mat_efect_cont = None
        # raster contains surface slopes data
        cls.mat_slope = None
        # raster labels not a number cells
        cls.mat_nan = None
        # raster contains parameters ...
        cls.mat_a = None
        # raster contains parameters ...
        cls.mat_n = None
        # ???
        cls.points = None
        # end time of computation
        cls.end_time = None
        # raster contains cell flow state information
        cls.state_cell = None
        # bool variable for flow direction algorithm (false=one direction, true
        # multiple flow direction)
        cls.mfda = None
        # list contains the precipitation data
        cls.sr = None
        # counter of precipitation intervals
        cls.itera = None
        # ???
        cls.streams = None
        # ???
        cls.cell_stream = None
        # raster contains the reach id data
        cls.mat_stream_reach = None
        # ???
        cls.STREAM_RATIO = None
        # maximum allowed time step during compuation
        cls.maxdt = None
        # if true extra data are stores in the point*.dat files
        cls.extraOut = None
        # stream magic number
        cls.streams_flow_inc = 1000
        # no segment downside
        cls.streamsNextDownIdNoSegment = -1
        # slope width
        cls.slope_width = None
