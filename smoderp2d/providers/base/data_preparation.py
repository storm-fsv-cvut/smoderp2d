import os
import shutil
import numpy as np
from abc import ABC, abstractmethod

from smoderp2d.processes import rainfall
from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers.base import Logger
from smoderp2d.providers.base.exceptions import DataPreparationError, DataPreparationInvalidInput

class PrepareDataBase(ABC):
    def __init__(self, writter):
        self.storage = writter

        # complete dictionary of datasets and their type
        self._data_layers = {
            'dem_slope_mask' : 'temp',
            'dem_polygon': 'temp',
            'aoi': 'temp',
            'aoi_polygon': 'core',
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
            "stream_Z": 'temp',
            'stream_start': 'temp',
            'stream_end': 'temp',
            'stream_seg': 'temp',
            'ratio_cell' : 'temp',
            'efect_cont' : 'temp',

            'veg_fieldname': "veg_type",
        }
        self.soilveg_fields = {
            "k": None, "s": None, "n": None, "pi": None, "ppl": None,
            "ret": None, "b": None, "x": None, "y": None, "tau": None, "v": None
        }
        for sv in self.soilveg_fields.keys():
            self._data_layers["soilveg_aoi_{}".format(sv)] = 'temp'
        self.storage.set_data_layers(self._data_layers)

        self.stream_shape_fields = [
            "number", self._input_params['table_stream_shape_code'],
            "shapetype", "b", "m", "roughness", "q365"
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
            'mat_efect_cont': None,
            'mat_slope': None,
            'mat_nan': None,
            'mat_a': None,
            'mat_n': None,
            'poradi': None,
            'end_time': self._input_params['end_time'],
            'state_cell': None,
            'temp': None,
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
        prevent time consuming operations on DEM if the DEM is much
        larger then the AOI.

        :param dem: string path to DEM layer

        :return: string paths to DEM derivates
        """
        pass

    @abstractmethod
    def _clip_raster_layer(self, dataset, outline, name):
        """Clips raster dataset to given polygon.

        :param dataset: raster dataset to be clipped
        :param aoi_polygon: feature class to be used as the clipping geometry
        :param name: dataset name in the _data dictionary

        :return: full path to clipped raster
        """
        pass

    @abstractmethod
    def _clip_record_points(self, dataset, outline, name):
        """Makes a copy of record points inside the AOI as new
        feature layer and logs those outside AOI.

        :param dataset: points dataset to be clipped
        :param aoi_polygon: polygon feature class of the AoI
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
    def _update_grid_globals(self, reference):
        """Update raster spatial reference info.

        This function must be called before _rst2np() is used first
        time.

        :param reference: reference raster layer
        """
        pass

    @abstractmethod
    def _compute_efect_cont(self, dem_clip):
        """Compute efect contour array.
        ML: improve description
        
        :param dem: string to dem clipped by area of interest
        :param asp: sting to aspect clipped by area of interest
        :return: numpy array
        """
        pass

    @abstractmethod    
    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_outline, table_soil_vegetation):
        """Prepares the combination of soils and vegetation input
        layers. Gets the spatial intersection of both and checks the
        consistency of attribute table.

        :param soil: string path to soil layer
        :param soil_type: soil type attribute
        :param vegetation: string path to vegetation layer
        :param vegetation_type: vegetation type attribute
        :param aoi_polygon: string path to polygon layer defining area of interest
        :param table_soil_vegetation: string path to table with soil and vegetation attributes
        
        :return: full path to soil and vegetation dataset
        """
        pass

    @abstractmethod
    def _get_array_points(self):
        """Get array of points. Points near AOI border are skipped.

        :return: generated numpy array
        """
        pass

    @abstractmethod
    def _stream_clip(self, stream, aoi_polygon):
        """Clip stream layer to the given polygon.

        :param stream: path to stream layer
        :param outline: path to polygon layer of the AoI

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
    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        """Compute shape of stream.

        :param stream: string path to stream dataset
        :param stream_shape_code: shape code column
        :param stream_shape_tab: table with stream shapes

        :return list: stream shape attributes as list
        """
        pass

    @abstractmethod
    def _check_input_data(self):
        """Check input data.

        Raise DataPreparationInvalidInput on error.
        """
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
        aoi_polygon = self._create_AoI_outline(
            self._input_params['elevation'],
            self._input_params['soil'],
            self._input_params['vegetation']
        )
        Logger.progress(10)

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
        dem_aoi = self._clip_raster_layer(dem_filled, aoi_polygon, 'dem_aoi')
        dem_flowdir_aoi = self._clip_raster_layer(dem_flowdir, aoi_polygon, 'dem_flowdir_aoi')
        self._clip_raster_layer(dem_flowacc, aoi_polygon, 'dem_flowacc_aoi')
        dem_slope_aoi = self._clip_raster_layer(dem_slope, aoi_polygon, 'dem_slope_aoi')
        dem_aspect_aoi = self._clip_raster_layer(dem_aspect, aoi_polygon, 'dem_aspect_aoi')
        points_aoi = self._clip_record_points(self._input_params['points'], aoi_polygon, 'points_aoi')
        Logger.progress(30)

        # convert to numpy arrays
        self.data['mat_dem'] = self._rst2np(dem_aoi)
        # update data dict for spatial ref info
        GridGlobals.r = self.data['mat_dem'].shape[0]
        GridGlobals.c = self.data['mat_dem'].shape[1]
        self._update_grid_globals(dem_aoi)
        if GridGlobals.dx != GridGlobals.dy:
            raise DataPreparationInvalidInput(
                "Input DEM spatial x resolution ({}) differs from y resolution ({}). "
                "Resample input data to set the same x and y spatial resolution before "
                "running SMODERP2D.".format(GridGlobals.dx, GridGlobals.dy))
        self.data['mat_slope'] = self._rst2np(dem_slope_aoi)
        # unit conversion % -> 0-1
        self._convert_slope_units()
        if dem_flowdir_aoi is not None:
            self.data['mat_fd'] = self._rst2np(dem_flowdir_aoi)
        self.data['mat_efect_cont'] = self._compute_efect_cont(dem_aoi, dem_aspect_aoi)

        #   join the attributes to soil_veg intersect and check the table consistency
        Logger.info("Preparing soil and vegetation properties...")
        self._prepare_soilveg(
            self._input_params['soil'], self._input_params['soil_type'],
            self._input_params['vegetation'], self._input_params['vegetation_type'],
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

        # build points array
        Logger.info("Prepare points for hydrographs...")
        self.data['array_points'] = self._get_array_points()

        # build a/aa arrays
        self.data['mat_a'], self.data['mat_aa'] = self._get_a(
            self.soilveg_fields['n'], self.soilveg_fields['x'],
            self.soilveg_fields['y'], GridGlobals.r,
            GridGlobals.c, GridGlobals.NoDataValue, self.data['mat_slope']
        )
        Logger.progress(50)

        Logger.info("Computing critical level...")
        self.data['mat_hcrit'] = self._get_crit_water(
            self.data['mat_b'], self.soilveg_fields['tau'], self.soilveg_fields['v'], GridGlobals.r,
            GridGlobals.c, self.data['mat_slope'],
            GridGlobals.NoDataValue, self.data['mat_aa'])

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(self._input_params['rainfall_file'])
        Logger.progress(60)

        Logger.info("Processing stream network:")
        if self._input_params['stream'] and self._input_params['table_stream_shape'] and self._input_params['table_stream_shape_code']:
            self._prepare_stream(self._input_params['stream'],
                                 self._input_params['table_stream_shape'],
                                 self._input_params['table_stream_shape_code'],
                                 dem_aoi, aoi_polygon
            )
        Logger.progress(90)

        # define mask (rc/rc variables)
        self.data['mat_boundary'] = self._find_boundary_cells(
            GridGlobals.r, GridGlobals.c, GridGlobals.NoDataValue,
            self.data['mat_nan']
        )

        GridGlobals.rr, GridGlobals.rc = self._get_rr_rc(
            GridGlobals.r, GridGlobals.c, self.data['mat_boundary']
        )

        self.data['mfda'] = False ### ML: ???
        self.data['mat_boundary'] = None ## ML: -> JJ ???

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

        # create temporary dir
        self.data['temp'] = os.path.join(
            Globals.outdir, "temp"
        )
        Logger.debug(
            "Creating temp directory <{}>".format(self.data['temp'])
        )
        os.makedirs(self.data['temp'])

        # create control dir
        control = os.path.join(
            Globals.outdir, "control"
        )
        Logger.debug(
            "Creating control directory <{}>".format(control)
        )
        os.makedirs(control)

        self.storage.create_storage(self._input_params['output'])

    @staticmethod
    def _get_inf_combinat_index(r, c, mat_k, mat_s):
        """

        :param sfield:
        :param intersect:

        :return all_atrib:
        """
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
                    except:
                        combinat.append(ccc)
                        combinatIndex.append(
                            [combinat.index(ccc), kkk, sss, 0]
                        )
                        mat_inf_index[i][j] = combinat.index(
                            ccc
                        )

        return mat_inf_index, combinatIndex

    def _get_array_points_(self, array_points, x, y, fid, i):
        """Internal method called by _get_array_points().
        """
        # position i,j in raster (starts at 0)
        r = int(GridGlobals.r - ((y - GridGlobals.yllcorner) // GridGlobals.dy) - 1)
        c = int((x - GridGlobals.xllcorner) // GridGlobals.dx)

        # if point is not on the edge of raster or its
        # neighbours are not "NoDataValue", it will be saved
        # into array_points array
        nv = GridGlobals.NoDataValue
        if r != 0 and r != GridGlobals.r \
           and c != 0 and c != GridGlobals.c and \
           self.data['mat_dem'][r][c]   != nv and \
           self.data['mat_dem'][r-1][c] != nv and \
           self.data['mat_dem'][r+1][c] != nv and \
           self.data['mat_dem'][r][c-1] != nv and \
           self.data['mat_dem'][r][c+1] != nv:

            array_points[i][0] = fid
            array_points[i][1] = r
            array_points[i][2] = c
            # x,y coordinates of current point stored in an array
            array_points[i][3] = x
            array_points[i][4] = y
        else:
            Logger.info(
                "Point FID = {} is at the edge of the raster. "
                "This point will not be included in results.".format(fid))

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

    def _get_crit_water(self, mat_b, mat_tau, mat_v, r, c, mat_slope,
                        no_data_value, mat_aa):
        """

        :param all_attrib:
        """
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
                        hcrit_tau = hcrit_v = hcrit_flux = 1000 # set come auxiliary high value for zero slope

                    else:
                        hcrit_v = np.power((v_crit / aa), exp)  # h critical from v
                        hcrit_tau = tau_crit / 9807 / slope  # h critical from tau
                        hcrit_flux = np.power((flux_crit / slope / 9807 / aa),(1 / mat_b[i][j]))  # kontrola jednotek

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

    def _get_mat_nan(self, r, c, no_data_value, mat_slope, mat_dem):
        # vyrezani krajnich bunek, kde byly chyby, je to vyrazeno u
        # sklonu a acc
        mat_nan = np.zeros(
            [r, c], float
        )

        i = j = 0

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

    def _prepare_stream(self, stream, stream_shape_tab, stream_shape_code, dem_aoi, aoi_polygon):
        self.data['type_of_computing'] = 1

        # pocitam vzdy s ryhama pokud jsou zadane vsechny vstupy pro
        # vypocet toku, streams se pocitaji a type_of_computing je 3
        listin = [self._input_params['stream'],
                  self._input_params['table_stream_shape'],
                  self._input_params['table_stream_shape_code']]
        tflistin = [len(i) > 1 for i in listin] ### TODO: ???

        if all(tflistin):
            self.data['type_of_computing'] = 3

        if self.data['type_of_computing'] in (3, 5):
            Logger.info("Clipping stream to AoI outline ...")
            stream_aoi = self._stream_clip(stream, aoi_polygon)
            Logger.progress(70)

            Logger.info("Computing stream direction and inclinations...")
            self._stream_direction(stream_aoi, dem_aoi)
            Logger.progress(75)

            Logger.info("Computing stream segments...")
            self.data['mat_stream_reach'] = self._stream_reach(stream_aoi)
            Logger.progress(80)

            Logger.info("Computing stream hydraulics...")
            #self._stream_hydraulics(stream_aoi) # ML: is it used -> output ?
            self.data['streams'] = self._stream_shape(stream_aoi, stream_shape_code, stream_shape_tab)
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

        rr = []
        rc = []

        nv = no_data_value
        for i in nr:
            for j in nc:
                val = mat_nan[i][j]
                if i == 0 or j == 0 or i == (r - 1) or j == (c - 1):
                    if val != nv:
                        val = -99
                else:
                    if val != nv:
                        if  mat_nan[i - 1][j] == nv or \
                            mat_nan[i + 1][j] == nv or \
                            mat_nan[i][j - 1] == nv or \
                            mat_nan[i][j - 1] == nv:
                            val = -99
                        if  mat_nan[i - 1][j + 1] == nv or \
                            mat_nan[i + 1][j + 1] == nv or \
                            mat_nan[i - 1][j - 1] == nv or \
                            mat_nan[i + 1][j - 1] == nv:

                            val = -99.

                mat_boundary[i][j] = val

        return mat_boundary

    @staticmethod
    def _get_rr_rc(r, c, mat_boundary):
        """Create list rr and list of lists rc which contain i and j index of
        elements inside the compuation domain."""
        nr = range(r)
        nc = range(c)

        rr = []
        rc = []

        in_domain = False
        in_boundary = False

        for i in nr:
            one_col = []
            one_col_boundary = []
            for j in nc:

                if mat_boundary[i][j] == -99 and in_boundary is False:
                    in_boundary = True

                if mat_boundary[i][j] == -99 and in_boundary is True:
                    one_col_boundary.append(j)

                if (mat_boundary[i][j] == 0.0) and in_domain is False:
                    rr.append(i)
                    in_domain = True

                if (mat_boundary[i][j] == 0.0) and in_domain is True:
                    one_col.append(j)

            in_domain = False
            in_boundary = False
            rc.append(one_col)

        return rr, rc

    def _convert_slope_units(self):
        """
        Converts slope units from % to 0-1 range in the mask.
        """
        for i in range(self.data['mat_slope'].shape[0]):
            for j in range(self.data['mat_slope'].shape[1]):
                nv = GridGlobals.NoDataValue
                if self.data['mat_slope'][i][j] != nv:
                    self.data['mat_slope'][i][j] = self.data['mat_slope'][i][j]/100.

    def _get_mat_stream_seg(self, mat_stream_seg):
        # each element of stream has a number assigned from 0 to
        # no. of stream parts
        for i in range(GridGlobals.r):
            for j in range(GridGlobals.c):
                if mat_stream_seg[i][j] > 0: # FID starts at 1
                    # state 0|1|2 (> Globals.streams_flow_inc -> stream flow)
                    mat_stream_seg[i][j] += Globals.streams_flow_inc

    def _check_soilveg_dim(self, field):
        if self.soilveg_fields[field].shape[0] != GridGlobals.r or \
           self.soilveg_fields[field].shape[1] != GridGlobals.c:
            raise DataPreparationError(
                "Unexpected soilveg {} attribute array dimension {}: should be ({}, {})".format(
                    field, self.soilveg_fields[field].shape,
                    GridGlobals.r, GridGlobals.c)
            )

    def _stream_attr_(self, fid):
        fields = [fid, 'next_down_id', 'shape_length', 'inclination'] + self.stream_shape_fields
        
        stream_attr = {}
        for f in fields:
            stream_attr[f] = []

        return stream_attr
    def _check_input_data_(self):
        if self._input_params['stream'] or self._input_params['table_stream_shape'] or self._input_params['table_stream_shape_code']:
            if not self._input_params['stream']:
                raise DataPreparationInvalidInput("Option 'Reach feature layer' must be defined")
            if not self._input_params['table_stream_shape']:
                raise DataPreparationInvalidInput("Option 'Reach shape table' must be defined")
            if not self._input_params['table_stream_shape_code']:
                raise DataPreparationInvalidInput("Option 'Field with the reach feature identifier' must be defined")
