import os
import shutil
import numpy as np
from abc import ABC, abstractmethod

from smoderp2d.processes import rainfall
from smoderp2d.core.general import GridGlobals, Globals
from smoderp2d.providers.base import Logger

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
            'br': None,
            'bc': None,
            'mat_boundary': None,
            'rr': None,
            'rc': None,
            'outletCells': None,
            'xllcorner': None,
            'yllcorner': None,
            'array_points': None,
            'c': None,
            'r': None,
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
            'outdir': self._input_params['output'],
            'pixel_area': None,
            'points': self._input_params['points'], # TODO: needs to be replaced by the clipped points dataset
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
            'streams_loc': None
            }

    @abstractmethod
    def _create_AoI_outline(self, elevation, soil, vegetation):
        """Creates geometric intersection of input DEM, soil
        definition and landuse definition that will be used as Area of
        Interest outline. Slope is not created yet, but generally the
        edge pixels have nonsense values so "one pixel shrinked DEM"
        extent is used instead.
        """
        pass

    @abstractmethod    
    def _create_DEM_derivatives(self, dem):
        """Creates all the needed DEM derivatives in the DEM's
        original extent to avoid raster edge effects. The clipping
        extent could be replaced be AOI border buffered by 1 cell to
        prevent time consuming operations on DEM if the DEM is much
        larger then the AOI.
        """
        pass

    @abstractmethod
    def _clip_raster_layer(self, dataset, outline, name):
        """Clips raster dataset to given polygon."""
        pass

    @abstractmethod
    def _clip_record_points(self, dataset, outline, name):
        """Makes a copy of record points inside the AOI as new
        feature layer and logs those outside AOI.
        """
        pass

    @abstractmethod    
    def _prepare_soilveg(self, soil, soil_type, vegetation, vegetation_type,
                         aoi_outline, table_soil_vegetation):
        """Prepares the combination of soils and vegetation input
        layers. Gets the spatial intersection of both and checks the
        consistency of attribute table.
        """
        pass

    @abstractmethod
    def _rst2np(self, raster):
        """Convert raster data into numpy array."""
        pass

    @abstractmethod
    def _update_raster_dim(self, reference):
        """Update raster spatial reference info.

        This function must be called before _rst2np() is used first
        time.
        """
        pass

    @abstractmethod
    def _get_array_points(self):
        pass

    @abstractmethod
    def _compute_efect_cont(self, dem_clip):
        """Compute efect contour array.
        """
        pass

    @abstractmethod
    def _stream_clip(self, stream, aoi_polygon):
        pass

    @abstractmethod
    def _stream_direction(self, stream, dem_aoi):
        pass

    @abstractmethod
    def _stream_reach(self, stream):
        pass

    @abstractmethod
    def _stream_slope(self, stream):
        pass

    @abstractmethod
    def _stream_shape(self, stream, stream_shape_code, stream_shape_tab):
        pass

    @abstractmethod
    def _check_input_data(self):
        pass
            
    def run(self):
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
        # Logger.progress(10)

        # calculate DEM derivatives
        # intentionally done on non-clipped DEM to avoid edge effects
        Logger.info("Creating DEM-derived layers ...")
        dem_filled, dem_flowdir, dem_flowacc, dem_slope, dem_aspect = self._create_DEM_derivatives(
            self._input_params['elevation']
        )

        # prepare all needed layers for further processing
        #   clip the input layers to AIO outline including the record points
        Logger.info("Clipping layers to AoI outline ...")
        dem_aoi = self._clip_raster_layer(dem_filled, aoi_polygon, 'dem_aoi')
        dem_flowdir_aoi = self._clip_raster_layer(dem_flowdir, aoi_polygon, 'dem_flowdir_aoi')
        self._clip_raster_layer(dem_flowacc, aoi_polygon, 'dem_flowacc_aoi')
        dem_slope_aoi = self._clip_raster_layer(dem_slope, aoi_polygon, 'dem_slope_aoi')
        self._clip_raster_layer(dem_aspect, aoi_polygon, 'dem_aspect_aoi')
        points_aoi = self._clip_record_points(self._input_params['points'], aoi_polygon, 'points_aoi')

        # convert to numpy arrays
        self.data['mat_dem'] = self._rst2np(dem_aoi)
        # update data dict for spatial ref info
        self._update_raster_dim(dem_aoi)
        self.data['mat_slope'] = self._rst2np(dem_slope_aoi)
        # unit conversion % -> 0-1
        self._convert_slope_units()
        if dem_flowdir_aoi is not None:
            self.data['mat_fd'] = self._rst2np(dem_flowdir_aoi)
        self.data['mat_efect_cont'] = self._compute_efect_cont(dem_aoi)

        #   join the attributes to soil_veg intersect and check the table consistency
        Logger.info("Preparing soil and vegetation properties...")
        self._prepare_soilveg(
            self._input_params['soil'], self._input_params['soil_type'],
            self._input_params['vegetation'], self._input_params['vegetation_type'],
            aoi_polygon, self._input_params['table_soil_vegetation']
        )

        self.data['mat_inf_index'], self.data['combinatIndex'] = \
            self._get_inf_combinat_index(self.data['r'], self.data['c'],
                                         self.soilveg_fields['k'],
                                         self.soilveg_fields['s'])
        self.data['mat_n'] = self.soilveg_fields['n']
        self.data['mat_pi'] = self.soilveg_fields['pi']
        self.data['mat_ppl'] = self.soilveg_fields['ppl']
        self.data['mat_reten'] = self.soilveg_fields['ret']
        self.data['mat_b'] = self.soilveg_fields['b']

        self.data['mat_nan'], self.data['mat_slope'], self.data['mat_dem'] = \
            self._get_mat_nan(self.data['r'], self.data['c'],
                              GridGlobals.NoDataValue, self.data['mat_slope'],
                              self.data['mat_dem'])

        # build points array
        Logger.info("Prepare points for hydrographs...")
        self.data['array_points'] = self._get_array_points()

        # build a/aa arrays
        self.data['mat_a'], self.data['mat_aa'] = self._get_a(
            self.soilveg_fields['n'], self.soilveg_fields['x'],
            self.soilveg_fields['y'], self.data['r'],
            self.data['c'], GridGlobals.NoDataValue, self.data['mat_slope']
        )
        #Logger.progress(40)

        Logger.info("Computing critical level...")
        self.data['mat_hcrit'] = self._get_crit_water(
            self.data['mat_b'], self.soilveg_fields['tau'], self.soilveg_fields['v'], self.data['r'],
            self.data['c'], self.data['mat_slope'],
            GridGlobals.NoDataValue, self.data['mat_aa'])

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(self._input_params['rainfall_file'])

        #Logger.progress(50)

        Logger.info("Computing stream preparation...")
        # self._prepare_streams(aoi_polygon, dem_clip, intersect, flow_accumulation_clip)
        if self._input_params['stream'] and self._input_params['table_stream_shape'] and self._input_params['table_stream_shape_code']:
            self._prepare_stream(self._input_params['stream'],
                                 self._input_params['table_stream_shape'],
                                 self._input_params['table_stream_shape_code'],
                                 dem_aoi, aoi_polygon
            )

        # define mask (rc/rc variables)
        self.data['mat_boundary'] = self._find_boundary_cells(
            self.data['r'], self.data['c'], GridGlobals.NoDataValue,
            self.data['mat_nan']
        )

        self.data['rr'], self.data['rc'] = self._get_rr_rc(
            self.data['r'], self.data['c'], self.data['mat_boundary']
        )

        self.data['mfda'] = False ### ML: ???
        self.data['mat_boundary'] = None ## ML: ???
        #Logger.progress(100)

        Logger.info("Data preparation has been finished")
        Logger.info('-' * 80)

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
        if not self.data['outdir']:
            # no output directory defined, nothing to do
            return

        # delete output directory if exists and create new one
        Logger.info(
            "Creating output directories <{}>".format(self.data['outdir'])
        )
        if os.path.exists(self.data['outdir']):
            shutil.rmtree(self.data['outdir'])
        os.makedirs(self.data['outdir'])

        # create temporary dir
        self.data['temp'] = os.path.join(
            self.data['outdir'], "temp"
        )
        Logger.debug(
            "Creating temp directory <{}>".format(self.data['temp'])
        )
        os.makedirs(self.data['temp'])

        # create control dir
        control = os.path.join(
            self.data['outdir'], "control"
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
        r = int(self.data['r'] - ((y - self.data['yllcorner']) // self.data['dy']) - 1)
        c = int((x - self.data['xllcorner']) // self.data['dx'])

        # if point is not on the edge of raster or its
        # neighbours are not "NoDataValue", it will be saved
        # into array_points array
        nv = GridGlobals.NoDataValue
        if r != 0 and r != self.data['r'] \
           and c != 0 and c != self.data['c'] and \
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

        for out, arr in (("hcrit_tau", mat_hcrit_tau),
                         ("hcrit_flux", mat_hcrit_flux),
                         ("hcrit_v", mat_hcrit_v)):
            self.storage.write_raster(
                arr, out, 'temp'
            )
        self.storage.write_raster(
            mat_hcrit, 'mat_hcrit', ''
        )

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

        self.storage.write_raster(
            mat_nan,
            'mat_nan',
            'temp'
        )

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

            Logger.info("Computing stream direction and elevation...")
            self._stream_direction(stream_aoi, dem_aoi)

            Logger.info("Computing stream segments...")
            self.data['mat_stream_reach'] = self._stream_reach(stream_aoi)

            Logger.info("Computing stream hydraulics...")
            #self._stream_hydraulics(stream_aoi) # ML: is it used?
            self._stream_slope(stream_aoi)
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
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                if mat_stream_seg[i][j] > 0: # FID starts at 1
                    # state 0|1|2 (> Globals.streams_flow_inc -> stream flow)
                    mat_stream_seg[i][j] += Globals.streams_flow_inc
