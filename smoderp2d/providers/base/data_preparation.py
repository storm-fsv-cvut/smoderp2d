import os
import shutil
import math
import numpy as np
from abc import ABC, abstractmethod

from smoderp2d.processes import rainfall
from smoderp2d.core import CompType
from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationError, \
    DataPreparationInvalidInput


class PrepareDataBase(ABC):
    @staticmethod
    def _get_a(mat_n, mat_x, mat_y, r, c, no_data, mat_slope):
        """Build 'a' and 'aa' arrays.

        :param mat_n:
        :param mat_x:
        :param mat_y:
        :param r: number of rows
        :param c: number of columns
        :param no_data: no data value
        :param mat_slope:
        :return: np ndarray for mat_a and for mat_aa
        """
        mat_a = np.zeros(
            [r, c], float
        )
        mat_aa = np.zeros(
            [r, c], float
        )

        # calculating the "a" parameter
        for i in range(r):
            for j in range(c):
                slope = mat_slope[i][j]
                par_x = mat_x[i][j]
                par_y = mat_y[i][j]

                if par_x == no_data or par_y == no_data or slope == no_data:
                    par_a = no_data
                    par_aa = no_data
                elif par_x == no_data or par_y == no_data or slope == 0.0:
                    par_a = 0.0001
                    par_aa = par_a / mat_n[i][j]
                else:
                    exp = np.power(slope, par_y)
                    par_a = par_x * exp
                    par_aa = par_a / mat_n[i][j]

                mat_a[i][j] = par_a
                mat_aa[i][j] = par_aa

        return mat_a, mat_aa

    @staticmethod
    def _get_crit_water(mat_b, mat_tau, mat_v, r, c, mat_slope,
                        no_data_value, mat_aa):
        # critical water level
        mat_hcrit_tau = np.zeros([r, c], float)
        mat_hcrit_v = np.zeros([r, c], float)
        mat_hcrit_flux = np.zeros([r, c], float)
        mat_hcrit = np.zeros([r, c], float)

        for i in range(r):
            for j in range(c):
                if mat_slope[i][j] != no_data_value \
                   and mat_tau[i][j] != no_data_value:
                    slope = mat_slope[i][j]
                    tau_crit = mat_tau[i][j]
                    v_crit = mat_v[i][j]
                    b = mat_b[i][j]
                    aa = mat_aa[i][j]
                    flux_crit = tau_crit * v_crit
                    exp = 1 / (b - 1)

                    if slope == 0.0:
                        hcrit_tau = hcrit_v = hcrit_flux = 1000
                        # set come auxiliary high value for zero slope
                    else:
                        hcrit_v = np.power((v_crit / aa), exp)
                        # h critical from v
                        hcrit_tau = tau_crit / 9807 / slope
                        # h critical from tau
                        hcrit_flux = np.power(
                            (flux_crit / slope / 9807 / aa), (1 / mat_b[i][j])
                        )  # kontrola jednotek

                    mat_hcrit_tau[i][j] = hcrit_tau
                    mat_hcrit_v[i][j] = hcrit_v
                    mat_hcrit_flux[i][j] = hcrit_flux
                    hcrit = min(hcrit_tau, hcrit_v, hcrit_flux)
                    mat_hcrit[i][j] = hcrit
                else:
                    mat_hcrit_tau[i][j] = no_data_value
                    mat_hcrit_v[i][j] = no_data_value
                    mat_hcrit_flux[i][j] = no_data_value
                    mat_hcrit[i][j] = no_data_value

        return mat_hcrit

    @staticmethod
    def _get_inf_combinat_index(r, c, mat_k, mat_s):
        mat_inf_index = None
        combinatIndex = None

        infiltration_type = 0  # "Phillip"
        if infiltration_type == 0:
            # to se rovna vzdycky ne? nechapu tuhle podminku 23.05.2018 MK
            mat_inf_index = np.zeros(
                [r, c], int
            )
            combinat = []
            combinatIndex = []
            for i in range(r):
                for j in range(c):
                    kkk = mat_k[i][j]
                    sss = mat_s[i][j]
                    ccc = [kkk, sss]
                    try:
                        if combinat.index(ccc):
                            mat_inf_index[i][j] = combinat.index(ccc)
                    except ValueError:
                        # ccc not in combinat
                        combinat.append(ccc)
                        combinatIndex.append(
                            [combinat.index(ccc), kkk, sss, 0]
                        )
                        mat_inf_index[i][j] = combinat.index(
                            ccc
                        )

        return mat_inf_index, combinatIndex

    @staticmethod
    def _get_mat_nan(r, c, no_data_value, mat_slope, mat_dem):
        # vyrezani krajnich bunek, kde byly chyby, je to vyrazeno u
        # sklonu a acc
        mat_nan = np.zeros(
            [r, c], float
        )

        # data value vector intersection
        # TODO: no loop needed?
        nv = no_data_value
        for i in range(r):
            for j in range(c):
                x_mat_dem = mat_dem[i][j]
                slp = mat_slope[i][j]
                if x_mat_dem == nv or slp == nv:
                    mat_nan[i][j] = nv
                    mat_slope[i][j] = nv
                    mat_dem[i][j] = nv
                else:
                    mat_nan[i][j] = 0

        return mat_nan, mat_slope, mat_dem

    @staticmethod
    def _get_rr_rc(r, c, mat_boundary):
        """Create list rr and list of lists rc which contain i and j index of
        elements inside the compuation domain."""
        nr = range(r)
        nc = range(c)

        rr = []
        rc = []

        rr_insert = False

        for i in nr:
            one_col = []
            for j in nc:

                if mat_boundary[i][j] == -99:
                    one_col.append(j)
                    rr_insert = True

                elif mat_boundary[i][j] == 0.0:
                    one_col.append(j)
                    rr_insert = True

            if rr_insert is True:
                rr.append(i)
            rr_insert = False
            rc.append(one_col)

        return rr, rc


class PrepareDataGISBase(PrepareDataBase):
    def __init__(self, writter):
        self.storage = writter

        # complete dictionary of datasets and their type
        self._data_layers = {
            'dem_slope_mask': 'temp',
            'dem_polygon': 'temp',
            'aoi': 'temp',
            'aoi_polygon': 'core',
            'aoi_mask': 'temp',
            'dem_filled': 'temp',
            'dem_flowdir': 'temp',
            'dem_flowacc': 'temp',
            'dem_slope': 'temp',
            'dem_aspect': 'temp',
            'dem_aoi': 'temp',
            'dem_slope_aoi': 'temp',
            'dem_flowdir_aoi': 'temp',
            'dem_flowacc_aoi': 'temp',
            'dem_aspect_aoi': 'temp',
            'points_aoi': 'temp',
            'soil_veg': 'temp',
            'soilveg_aoi': 'temp',
            'aoi_buffer': 'temp',
            'stream_aoi': 'temp',
            "stream_z": 'temp',
            'stream_start': 'temp',
            'stream_end': 'temp',
            'stream_seg': 'temp',
            'ratio_cell': 'temp',
            'effect_cont': 'temp',
        }
        # complete list of field names that are supposed not to be changed,
        # e.g. in properties tables
        self.fieldnames = {
            'veg_type_fieldname': 'veg_type',
            'soilveg_type_fieldname': 'soilveg_type',
            'stream_segment_id': 'segment_id',
            'stream_segment_start_elevation': 'start_elev',
            'stream_segment_end_elevation': 'end_elev',
            'stream_segment_inclination': 'inclination',
            'stream_segment_next_down_id': 'next_down_id',
            'stream_segment_length': 'segment_length',
            'channel_shape_id':  self._input_params[
                'streams_channel_type_fieldname'
            ],
            'channel_profile': 'profile',
            'channel_shapetype': 'shapetype',
            'channel_bottom_width': 'b',
            'channel_bank_steepness': 'm',
            'channel_bed_roughness': 'roughness',
            'channel_q365': 'q365'
        }

        self.soilveg_fields = {
            "k": None, "s": None, "n": None, "pi": None, "ppl": None,
            "ret": None, "b": None, "x": None, "y": None, "tau": None, "v": None
        }
        for sv in self.soilveg_fields.keys():
            self._data_layers["soilveg_aoi_{}".format(sv)] = 'temp'
        self.storage.set_data_layers(self._data_layers)

        self.stream_shape_fields = [
            self.fieldnames['channel_profile'],
            self.fieldnames['channel_shapetype'],
            self.fieldnames['channel_bottom_width'],
            self.fieldnames['channel_bank_steepness'],
            self.fieldnames['channel_bank_steepness'],
            self.fieldnames['channel_bed_roughness'],
            self.fieldnames['channel_q365']
        ]

        self.data = {
            'mat_boundary': None,
            'outletCells': None,
            'array_points': None,
            'combinatIndex': None,
            'maxdt': self._input_params['maxdt'],
            'mat_pi': None,
            'mat_ppl': None,
            'surface_retention': None,
            'mat_inf_index': None,
            'mat_hcrit': None,
            'mat_aa': None,
            'mat_b': None,
            'mat_reten': None,
            'mat_fd': None,
            'mat_dem': None,
            'mat_effect_cont': None,
            'mat_slope': None,
            'mat_nan': None,
            'mat_a': None,
            'mat_n': None,
            'end_time': self._input_params['end_time'],
            'state_cell': None,
            'type_of_computing': None,
            'mfda': None,
            'sr': None,
            'itera': None,
            'streams': None,
            'cell_stream': None,
            'mat_stream_reach': None,
            'STREAM_RATIO': None,
            }

    @abstractmethod
    def _create_AoI_outline(self, elevation, soil, vegetation):
        """Creates geometric intersection of input DEM, soil
        definition and landuse definition that will be used as Area of
        Interest outline. Slope is not created yet, but generally the
        edge pixels have nonsense values so "one pixel shrinked DEM"
        extent is used instead.

        :param elevation: string path to DEM layer
        :param soil: string path to soil definition layer
        :param vegetation: string path to vegenatation definition layer

        :return: string path to AIO polygon layer
        """
        pass

    @abstractmethod
    def _create_DEM_derivatives(self, dem):
        """Creates all the needed DEM derivatives in the DEM's
        original extent to avoid raster edge effects. The clipping
        extent could be replaced be AOI border buffered by 1 cell to
        prevent time-consuming operations on DEM if the DEM is much
        larger than the AOI.

        :param dem: string path to DEM layer

        :return: string paths to DEM derivates
        """
        pass

    @abstractmethod
    def _clip_raster_layer(self, dataset, aoi_mask, name):
        """Clips raster dataset to given polygon.

        :param dataset: raster dataset to be clipped
        :param name: dataset name in the _data dictionary

        :return: full path to clipped raster
        """
        pass

    @abstractmethod
    def _clip_record_points(self, dataset, aoi_polygon, name):
        """Makes a copy of record points inside the AOI as new
        feature layer and logs those outside AOI.

        :param dataset: points dataset to be clipped
        :param name: output dataset name in the _data dictionary

        :return: full path to clipped points dataset
        """
        pass

    @abstractmethod
    def _rst2np(self, raster):
        """Convert raster data into numpy array.

        :param raster: raster name

        :return: numpy array
        """
        pass

    @abstractmethod
    def _update_grid_globals(self, reference, reference_cellsize=None):
        """Update raster spatial reference info.

        This function must be called before _rst2np() is used first
        time.

        :param reference: reference raster layer
        :param reference_cellsize: reference raster layer for cell size (see https://github.com/storm-fsv-cvut/smoderp2d/issues/256)
        """
        pass

    @abstractmethod
    def _compute_effect_cont(self, dem, asp):
        """Compute effect contour array.

        ML: improve description.

        :param dem: string to dem clipped by area of interest
        :return: numpy array
        """
        pass

    @abstractmethod
    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_polygon, table_soil_vegetation):
        """Prepare the combination of soils and vegetation input layers.

        Gets the spatial intersection of both and checks the
        consistency of attribute table.

        :param soil: string path to soil layer
        :param soil_type: soil type attribute
        :param vegetation: string path to vegetation layer
        :param vegetation_type: vegetation type attribute
        :param table_soil_vegetation: string path to table with soil and
                                      vegetation attributes

        :return: full path to soil and vegetation dataset
        """
        pass

    @abstractmethod
    def _get_points_location(self, points_layer):
        """Get array of points locations.

        X and Y coordinates are obtained from the input points geometry
        points' row and column index in the dem_aoi is calculated

        :return: array with point fids, dem row and column indexes and
                 x, y coordinates
        """
        pass

    @abstractmethod
    def _stream_clip(self, stream, aoi_polygon):
        """Clip stream layer to the given polygon.

        :param stream: path to stream layer
        :param aoi_polygon: path to polygon layer of the AoI

        :return: full path to clipped stream dataset
        """
        pass

    @abstractmethod
    def _stream_direction(self, stream, dem):
        """Compute elevation of start/end point of stream parts.
        Add code of ascending stream part into attribute table.

        :param stream: string path to stream dataset
        :param dem: string path to DEM dataset
        """
        pass

    @abstractmethod
    def _stream_reach(self, stream):
        """Get numpy array of integers detecting whether there is a stream on
        corresponding pixel of raster (number equal or greater than
        1000 in return numpy array) or not (number 0 in return numpy
        array).

        :param stream: string path to stream dataset

        :return mat_stream_seg: Numpy array
        """
        pass
    #
    # @abstractmethod
    # def _stream_slope(self, stream):
    #     """Compute slope of stream
    #
    #     :param stream: string path to stream dataset
    #     """
    #     pass

    @abstractmethod
    def _stream_shape(self, streams, channel_shape_code,
                      channel_properties_table):
        """Compute shape of stream.

        :param streams: string path to streams dataset
        :param channel_shape_code: shape code column
        :param channel_properties_table: table with stream shapes

        :return list: stream shape attributes as list
        """
        pass

    @abstractmethod
    def _check_input_data(self):
        """Check input data.

        Raise DataPreparationInvalidInput on error.
        """
        pass

    @abstractmethod
    def _get_field_names(self, ds):
        """Get field names for vector layer."""
        pass

    @abstractmethod
    def _check_empty_values(self, table, field):
        """Check empty values in fields."""
        pass

    def run(self):
        """Perform data preparation steps.

        :return dict: prepared data as dictionary
        """
        Logger.info('-' * 80)
        Logger.info("DATA PREPARATION")

        # check input data (overlaps)
        self._check_input_data()

        # create output folder, where temporary data are stored
        self._create_output_dir()

        # intersect the input datasest to define the area of interest
        Logger.info("Creating intersect of input datasets ...")
        aoi_polygon, aoi_mask = self._create_AoI_outline(
            self._input_params['elevation'],
            self._input_params['soil'],
            self._input_params['vegetation']
        )
        Logger.progress(10)

        # set GridGlobals
        self._update_grid_globals(aoi_mask, self._input_params['elevation'])
        if GridGlobals.dx != GridGlobals.dy:
            raise DataPreparationInvalidInput(
                "Input DEM spatial x resolution ({}) differs from y "
                "resolution ({}). Resample input data to set the same x and y"
                " spatial resolution before running SMODERP2D.".format(
                    GridGlobals.dx, GridGlobals.dy)
            )

        # calculate DEM derivatives
        # intentionally done on non-clipped DEM to avoid edge effects
        Logger.info("Creating DEM-derived layers...")
        dem_filled, dem_flowdir, dem_flowacc, dem_slope, dem_aspect = self._create_DEM_derivatives(
            self._input_params['elevation']
        )
        Logger.progress(20)

        # prepare all needed layers for further processing
        #   clip the input layers to AIO outline including the record points
        Logger.info("Clipping layers to AoI outline...")
        dem_aoi = self._clip_raster_layer(dem_filled, aoi_mask, 'dem_aoi')
        dem_flowdir_aoi = self._clip_raster_layer(
            dem_flowdir, aoi_mask, 'dem_flowdir_aoi'
        )
        self._clip_raster_layer(dem_flowacc, aoi_mask, 'dem_flowacc_aoi')
        dem_slope_aoi = self._clip_raster_layer(
            dem_slope, aoi_mask, 'dem_slope_aoi'
        )
        dem_aspect_aoi = self._clip_raster_layer(
            dem_aspect, aoi_mask, 'dem_aspect_aoi'
        )
        # convert to numpy arrays
        self.data['mat_dem'] = self._rst2np(dem_aoi)
        self.data['mat_slope'] = self._rst2np(dem_slope_aoi)
        # unit conversion % -> 0-1
        self._convert_slope_units()
        if dem_flowdir_aoi is not None:
            self.data['mat_fd'] = self._rst2np(dem_flowdir_aoi)
        self.data['mat_effect_cont'] = self._compute_effect_cont(
            dem_aoi, dem_aspect_aoi
        )
        Logger.progress(30)

        # build points array
        if self._input_params['points'] != '':
            points_aoi = self._clip_record_points(
                self._input_params['points'], aoi_polygon, 'points_aoi'
            )
            Logger.info("Preparing points for hydrographs...")
            self.data['array_points'] = self._get_points_location(points_aoi)

        #   join the attributes to soil_veg intersect and check the table
        #   consistency
        Logger.info("Preparing soil and vegetation properties...")
        self._prepare_soilveg(
            self._input_params['soil'],
            self._input_params['soil_type_fieldname'],
            self._input_params['vegetation'],
            self._input_params['vegetation_type_fieldname'],
            aoi_polygon, self._input_params['table_soil_vegetation']
        )
        Logger.progress(40)

        self.data['mat_n'] = self.soilveg_fields['n']
        self.data['mat_pi'] = self.soilveg_fields['pi']
        self.data['mat_ppl'] = self.soilveg_fields['ppl']
        self.data['mat_reten'] = self.soilveg_fields['ret']
        self.data['mat_b'] = self.soilveg_fields['b']

        self.data['mat_inf_index'], self.data['combinatIndex'] = \
            self._get_inf_combinat_index(GridGlobals.r, GridGlobals.c,
                                         self.soilveg_fields['k'],
                                         self.soilveg_fields['s'])

        self.data['mat_nan'], self.data['mat_slope'], self.data['mat_dem'] = \
            self._get_mat_nan(GridGlobals.r, GridGlobals.c,
                              GridGlobals.NoDataValue, self.data['mat_slope'],
                              self.data['mat_dem'])

        # build a/aa arrays
        self.data['mat_a'], self.data['mat_aa'] = self._get_a(
            self.soilveg_fields['n'], self.soilveg_fields['x'],
            self.soilveg_fields['y'], GridGlobals.r,
            GridGlobals.c, GridGlobals.NoDataValue, self.data['mat_slope']
        )
        Logger.progress(50)

        Logger.info("Computing critical level...")
        self.data['mat_hcrit'] = self._get_crit_water(
            self.data['mat_b'], self.soilveg_fields['tau'],
            self.soilveg_fields['v'], GridGlobals.r,
            GridGlobals.c, self.data['mat_slope'],
            GridGlobals.NoDataValue, self.data['mat_aa'])
        self.storage.write_raster(self.data['mat_hcrit'], 'hcrit', 'control')

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(self._input_params['rainfall_file'])
        Logger.progress(60)

        Logger.info("Processing stream network:")
        if self._input_params['streams'] and self._input_params['channel_properties_table'] and self._input_params['streams_channel_type_fieldname']:
            self._prepare_streams(
                self._input_params['streams'],
                self._input_params['channel_properties_table'],
                self._input_params['streams_channel_type_fieldname'],
                dem_filled,
                # provide unclipped DEM to avoid stream vertices placed
                # outside DEM
                aoi_polygon
            )
        else:
            self.data['type_of_computing'] = CompType.rill

        Logger.progress(90)

        # define mask (rc/rc variables)
        self.data['mat_boundary'] = self._find_boundary_cells(
            GridGlobals.r, GridGlobals.c, GridGlobals.NoDataValue,
            self.data['mat_nan']
        )
        self.storage.write_raster(
            self.data['mat_boundary'], 'mat_boundary', 'temp'
        )

        GridGlobals.rr, GridGlobals.rc = self._get_rr_rc(
            GridGlobals.r, GridGlobals.c, self.data['mat_boundary']
        )

        self.data['mfda'] = False  # ML: ???
        self.data['mat_boundary'] = None  # ML: -> JJ ???

        Logger.info("Data preparation has been finished")
        Logger.info('-' * 80)
        Logger.progress(100)

        return self.data

    def _set_input_params(self, options):
        """Set input parameters from user-given options.

        :param options: directory with user-given options
        """
        self._input_params = options
        # cast some options to float
        for opt in ('maxdt', 'end_time'):
            self._input_params[opt] = float(self._input_params[opt])

    def _create_output_dir(self):
        """Creates empty output and temporary directories to which created
        files are saved.
        """
        if not Globals.outdir:
            # no output directory defined, nothing to do
            return

        # delete output directory if exists and create new one
        Logger.info(
            "Creating output directories <{}>".format(Globals.outdir)
        )
        if os.path.exists(Globals.outdir):
            shutil.rmtree(Globals.outdir)
        os.makedirs(Globals.outdir)

        # create temporary/control dir
        for dir_name in ("temp", "control"):
            dir_path = os.path.join(Globals.outdir, dir_name)
            Logger.debug(
                "Creating {} directory <{}>".format(dir_name, dir_path)
            )
            os.makedirs(dir_path)

        self.storage.create_storage(self._input_params['output'])

    def _get_points_dem_coords(self, x, y):
        """ Finds the raster row and column index for input x, y coordinates
        :param x: X coordinate of the point
        :param y: Y coordinate of the point

        :return: r, c - row and column index of the input point if point within
        the DEM, else None
        """
        # position i,j in raster (starts at 0)
        r = int(
            GridGlobals.r - ((y - GridGlobals.yllcorner) // GridGlobals.dy) - 1
        )
        c = int((x - GridGlobals.xllcorner) // GridGlobals.dx)

        # if point is not on the edge of raster or its
        # neighbours are not "NoDataValue", it will be returned
        nv = GridGlobals.NoDataValue
        if r != 0 and r != GridGlobals.r \
            and c != 0 and c != GridGlobals.c and \
            self.data['mat_dem'][r][c] != nv and \
            self.data['mat_dem'][r-1][c] != nv and \
            self.data['mat_dem'][r+1][c] != nv and \
            self.data['mat_dem'][r][c-1] != nv and \
            self.data['mat_dem'][r][c+1] != nv:

            return r, c
        else:
            return None

    def _prepare_streams(self, stream, stream_shape_tab, stream_shape_code,
                         dem, aoi_polygon):
        self.data['type_of_computing'] = CompType.rill

        # pocitam vzdy s ryhama pokud jsou zadane vsechny vstupy pro
        # vypocet toku, streams se pocitaji a type_of_computing je 3
        listin = [self._input_params['streams'],
                  self._input_params['channel_properties_table'],
                  self._input_params['streams_channel_type_fieldname']]
        tflistin = [len(i) > 1 for i in listin]  # TODO: ???

        if all(tflistin):
            self.data['type_of_computing'] = CompType.stream_rill

        if self.data['type_of_computing'] in (CompType.stream_rill, CompType.stream_subflow_rill):
            Logger.info("Clipping stream to AoI outline ...")
            stream_aoi = self._stream_clip(stream, aoi_polygon)
            Logger.progress(70)

            Logger.info("Computing stream direction and inclinations...")
            self._stream_direction(stream_aoi, dem)
            Logger.progress(75)

            Logger.info("Computing stream segments...")
            self.data['mat_stream_reach'] = self._stream_reach(stream_aoi)
            Logger.progress(80)

            Logger.info("Computing stream hydraulics...")
            # self._stream_hydraulics(stream_aoi) # ML: is it used -> output ?
            self.data['streams'] = self._stream_shape(
                stream_aoi, stream_shape_code, stream_shape_tab
            )
        else:
            self.data['streams'] = None
            self.data['mat_stream_reach'] = None

    @staticmethod
    def _find_boundary_cells(r, c, no_data_value, mat_nan):
        """
        ? TODO: is it used?
        """
        # Identification of cells at the domain boundary

        mat_boundary = np.zeros([r, c], float)

        nr = range(r)
        nc = range(c)

        nv = no_data_value
        for i in nr:
            for j in nc:
                val = mat_nan[i][j]
                if i == 0 or j == 0 or i == (r - 1) or j == (c - 1):
                    if val != nv:
                        val = -99
                else:
                    if val != nv:
                        if mat_nan[i - 1][j] == nv or \
                            mat_nan[i + 1][j] == nv or \
                            mat_nan[i][j - 1] == nv or \
                            mat_nan[i][j - 1] == nv:
                            val = -99
                        if mat_nan[i - 1][j + 1] == nv or \
                            mat_nan[i + 1][j + 1] == nv or \
                            mat_nan[i - 1][j - 1] == nv or \
                            mat_nan[i + 1][j - 1] == nv:

                            val = -99.

                mat_boundary[i][j] = val

        return mat_boundary

    def _convert_slope_units(self):
        """
        Converts slope units from % to 0-1 range in the mask.
        """
        # TODO convert to NumPy logic!!!
        for i in range(self.data['mat_slope'].shape[0]):
            for j in range(self.data['mat_slope'].shape[1]):
                nv = GridGlobals.NoDataValue
                if self.data['mat_slope'][i][j] != nv:
                    self.data['mat_slope'][i][j] /= 100.

    @staticmethod
    def _get_mat_stream_seg(mat_stream_seg):
        # each element of stream has a number assigned from 0 to
        # no. of stream parts
        for i in range(GridGlobals.r):
            for j in range(GridGlobals.c):
                if mat_stream_seg[i][j] > 0:  # FID starts at 1
                    # state 0|1|2 (> Globals.streams_flow_inc -> stream flow)
                    mat_stream_seg[i][j] += Globals.streams_flow_inc

    def _check_soilveg_dim(self, field):
        if self.soilveg_fields[field].shape[0] != GridGlobals.r or \
           self.soilveg_fields[field].shape[1] != GridGlobals.c:
            raise DataPreparationError(
                "Unexpected soilveg {} attribute array dimension {}: "
                "should be ({}, {})".format(
                    field, self.soilveg_fields[field].shape,
                    GridGlobals.r, GridGlobals.c)
            )

    def _get_streams_attr_(self):
        fields = [
            self.fieldnames['stream_segment_id'],
            self._input_params['streams_channel_type_fieldname'],
            self.fieldnames['stream_segment_next_down_id'],
            self.fieldnames['stream_segment_length'],
            self.fieldnames['stream_segment_inclination']
        ] + self.stream_shape_fields

        stream_attr = {}
        for f in fields:
            stream_attr[f] = []

        return stream_attr

    def _check_input_data_(self):
        self._check_empty_values(
            self._input_params['vegetation'],
            self._input_params['vegetation_type_fieldname']
        )
        self._check_empty_values(
            self._input_params['soil'],
            self._input_params['soil_type_fieldname']
        )

        if self._input_params['streams'] or \
           self._input_params['channel_properties_table'] or \
           self._input_params['streams_channel_type_fieldname']:
            if not self._input_params['streams']:
                raise DataPreparationInvalidInput(
                    "Input parameter 'Stream network feature layer' must be "
                    "defined!"
                )
            if not self._input_params['channel_properties_table']:
                raise DataPreparationInvalidInput(
                    "Input parameter 'Channel properties table' must be "
                    "defined!"
                )
            if not self._input_params['streams_channel_type_fieldname']:
                raise DataPreparationInvalidInput(
                    "Field containing the channel shape identifier must be "
                    "set!"
                )

            # check presence of needed fields in stream shape properties table
            fields = self._get_field_names(
                self._input_params['channel_properties_table']
            )
            for f in self.stream_shape_fields:
                if f not in fields:
                    raise DataPreparationInvalidInput(
                        "Field '{}' not found in '{}'\nProper columns codes "
                        "are: {}".format(
                            f, self._input_params['channel_properties_table'],
                            self.stream_shape_fields
                        )
                    )

            # check presence streams_channel_type_fieldname in streams
            for target in (self._input_params["streams"],
                           self._input_params['channel_properties_table']):
                fields = self._get_field_names(target)
                channel_type_fieldname = self._input_params[
                    "streams_channel_type_fieldname"
                ]
                if channel_type_fieldname not in fields:
                    raise DataPreparationInvalidInput(
                        "Field '{}' not found in '{}'".format(
                            channel_type_fieldname, target
                        )
                    )

    @staticmethod
    def _check_resolution_consistency(ewres, nsres):
        """Raise DataPreparationInvalidInput on different spatial resolution."""
        if not math.isclose(GridGlobals.dx, ewres) or not math.isclose(GridGlobals.dy, nsres):
            raise DataPreparationInvalidInput(
                "Input DEM spatial resolution ({}, {}) differs from processing "
                "spatial resolution ({}, {})".format(
                    GridGlobals.dx, GridGlobals.dy, ewres, nsres)
            )

    @staticmethod
    def _check_rst2np(arr):
        """Check numpy array consistency with GridGlobals
        
        Raise DataPreparationError() if array's shape is different from GridGlobals.
        """
        if arr.shape[0] != GridGlobals.r or arr.shape[1] != GridGlobals.c:
            raise DataPreparationError(
                "Data inconsistency ({},{}) vs ({},{})".format(
                arr.shape[0], arr.shape[1],
                GridGlobals.r, GridGlobals.c)
            )

    def _decode_stream_attr(self, attr):
        """Decode attribute names to fieldnames keys"""
        attr_decoded = {}
        for k, v in attr.items():
            key_decoded = list(self.fieldnames.keys())[
                list(self.fieldnames.values()).index(k)
            ]
            attr_decoded[key_decoded] = v

        return attr_decoded

    def _stream_check_fields(self, stream_aoi):
        fields = self._get_field_names(stream_aoi)
        duplicated_fields = []
        for f in fields:
            if f in self.stream_shape_fields:
                # arcpy.management.DeleteField(stream_aoi, f)
                duplicated_fields.append(f)

        # inform the user about deleted fields
        if len(duplicated_fields) > 0:
            Logger.warning(
                "The input stream feature class '{}' must not contain fields "
                "from the channel properties table '{}':".format(
                    os.path.basename(self._input_params["streams"]),
                    os.path.basename(
                        self._input_params["channel_properties_table"]
                    )
                )
            )
            for f in duplicated_fields:
                Logger.warning(
                    f"\tField '{f}' was deleted from the streams dataset."
                )

        return duplicated_fields

    @staticmethod
    def _update_points_array(array_points, i, fid, r, c, x, y):
        """Update array of points"""
        array_points[i][0] = fid
        array_points[i][1] = r
        array_points[i][2] = c
        # x,y coordinates of current point stored in an array
        array_points[i][3] = x
        array_points[i][4] = y
