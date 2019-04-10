import os
import shutil
import numpy as np

import smoderp2d.processes.rainfall as rainfall

from smoderp2d.providers.base import Logger

class PrepareDataBase(object):
    def __init__(self):
        # internal output data
        self._data = {
            'dem_mask' : 'dem_mask',
            'ratio_cell' : 'ratio_cell',
            'efect_cont' : 'efect_cont',
            'soil_boundary': 'soil_b',
            'vegetation_boundary': 'vegetation_b',
            'vector_mask': 'dem_mask',
            'vegetation_mask': 'vegetation_mask',
            'soil_mask': 'soil_mask',
            'intersect': 'inter_soil_lu',
            'soil_veg_column': 'soil_veg',
            'soil_veg_copy': 'soil_veg_tab_current',
            'sfield': ["k", "s", "n", "pi", "ppl",
                       "ret", "b", "x", "y", "tau", "v"],
            'points_mask' : 'points_inter',
            'inter_mask' : 'inter_mask',
            'dem_clip' : 'dem_inter',
            'slope_clip' : 'slope_inter',
            'flow_clip' : 'flowdir_inter',
        }

        # primary key (is defined by provider)
        self._primary_key = None

    def run(self):
        Logger.info('-' * 80)
        Logger.info("DATA PREPARATION")

        # set output data directory
        self._set_output_data()

        # create output folder, where temporary data are stored
        self._set_output() 
        dem_copy, dem_mask = self._set_mask()

        # DTM computation
        Logger.info(
            "Computing fill, flow direction, flow accumulation, slope..."
        )
        dem_fill, flow_direction, flow_accumulation, slope = \
            self._terrain_products(dem_copy)

        # intersect
        Logger.info("Computing intersect of input data...")
        intersect, mask_shp, sfield = self._get_intersect(
            dem_copy, dem_mask,
            self._input_params['vegetation'],
            self._input_params['soil'],
            self._input_params['vegetation_type'],
            self._input_params['soil_type'],
            self._input_params['table_soil_vegetation'],
            self._input_params['table_soil_vegetation_code']
        )

        # clip
        Logger.info("Clip of the source data by intersect...")
        dem_clip, slope_clip, flow_direction_clip = self._clip_data(
            dem_copy, intersect, slope, flow_direction)

        # raster to numpy array conversion
        Logger.info("Computing parameters of DTM...")
        self.data['mat_dem'] = self._rst2np(dem_clip)
        self.data['mat_slope'] = self._rst2np(slope_clip)
        if flow_direction_clip is not None:
            self.data['mat_fd'] = self._rst2np(flow_direction_clip)
            self._save_raster("fl_dir",
                              self.data['mat_fd'],
                              self.data['temp']
            )

        # update data dict for spatial ref info
        self._get_raster_dim(dem_clip)

        # build numpy array from selected attributes
        all_attrib = self._get_mat_par(sfield, intersect)

        # build points array
        self._get_array_points()

        # build a/aa arrays
        self._get_a(all_attrib)

        Logger.info("Computing critical level...")
        self._get_crit_water(all_attrib)

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(self._input_params['rainfall_file'])

        # compute aspect
        self._get_slope_dir(dem_clip)

        Logger.info("Computing stream preparation...")
        self._prepare_streams(mask_shp, dem_clip, intersect
        )

        # ?
        self._find_boundary_cells()

        self.data['mat_n'] = all_attrib[2]
        self.data['mat_ppl'] = all_attrib[3]
        self.data['mat_pi'] = all_attrib[4]
        self.data['mat_reten'] = all_attrib[5]
        self.data['mat_b'] = all_attrib[6]

        self.data['mfda'] = False
        self.data['mat_boundary'] = None
        self.data['points'] = None
        self.data['spix'] = None
        self.data['vpix'] = None

        Logger.info("Data preparation has been finished")
        Logger.info('-' * 80)

        return self.data

    def _set_output_data(self):
        """
        Creates dictionary to which model parameters are computed.
        """
        # output data
        self.data = {
            'br': None,
            'bc': None,
            'mat_boundary': None,
            'rr': None,
            'rc': None,
            'outletCells': None,
            'xllcorner': None,
            'yllcorner': None,
            'NoDataValue': None,
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
            'points': self._input_params['points'], # TODO: used outside?
            'poradi': None,
            'end_time': self._input_params['end_time'],
            'spix': None,
            'state_cell': None,
            'temp': None,
            'type_of_computing': None,
            'vpix': None,
            'mfda': None,
            'sr': None,
            'itera': None,
            'toky': None,
            'cell_stream': None,
            'mat_tok_reach': None,
            'STREAM_RATIO': None,
            'toky_loc': None
            }

    def _set_output(self):
        """Creates empty output and temporary directories to which created
        files are saved.
        """
        if not self.data['outdir']:
            # no output directory defined, nothing to do
            return

        # delete output directory if exists and create new one
        Logger.info(
            "Creating output directory <{}>".format(self.data['outdir'])
        )
        if os.path.exists(self.data['outdir']):
            shutil.rmtree(self.data['outdir'])
        os.makedirs(self.data['outdir'])

        # create temporary dir
        Logger.debug(
            "Creating temp directory {}".format(self.data['temp'])
        )
        self.data['temp'] = os.path.join(
            self.data['outdir'], "temp"
        )
        os.makedirs(self.data['temp'])
        
    def _set_mask(self):
        raise NotImplemented("Not implemented for base provider")
    
    def _terrain_products(self, dem):
        raise NotImplemented("Not implemented for base provider")

    def _get_intersect(self, dem_copy, mask, vegetation, soil,
                       vegetation_type, soil_type,
                       table_soil_vegetation, table_soil_vegetation_code):
        raise NotImplemented("Not implemented for base provider")

    def _get_input_params(self):
        raise NotImplemented("Not implemented for base provider")

    def _rst2np(self, raster):
        raise NotImplemented("Not implemented for base provider")

    def _get_attrib(self, sfield, intersect):
        raise NotImplemented("Not implemented for base provider")

    def _get_attrib_(self, sfield, intersect):
        """Internal method. Called by _get_attrib().
        """
        dim = [self.data['r'], self.data['c']]

        mat_k = np.zeros(dim, float)
        mat_s = np.zeros(dim, float)
        mat_n = np.zeros(dim, float)
        mat_ppl = np.zeros(dim, float)
        mat_pi = np.zeros(dim, float)
        mat_ret = np.zeros(dim, float)
        mat_b = np.zeros(dim, float)
        mat_x = np.zeros(dim, float)
        mat_y = np.zeros(dim, float)
        mat_tau = np.zeros(dim, float)
        mat_v = np.zeros(dim, float)

        return [
            mat_k,
            mat_s,
            mat_n,
            mat_ppl,
            mat_pi,
            mat_ret,
            mat_b,
            mat_x,
            mat_y,
            mat_tau,
            mat_v
        ]

    def _get_mat_par(self, sfield, intersect):
        """

        :param sfield:
        :param intersect:

        :return all_atrib:
        """
        all_attrib = self._get_attrib(sfield, intersect)

        self.data['mat_nan'] = np.zeros(
            [self.data['r'], self.data['c']], float
        )

        mat_k = all_attrib[0]
        mat_s = all_attrib[1]

        self.data['mat_inf_index'] = None
        self.data['combinatIndex'] = None

        infiltration_type = 0  # "Phillip"
        if infiltration_type == 0:
            # to se rovna vzdycky ne? nechapu tuhle podminku 23.05.2018 MK
            self.data['mat_inf_index'] = np.zeros(
                [self.data['r'], self.data['c']], int
            )
            combinat = []
            self.data['combinatIndex'] = []
            for i in range(self.data['r']):
                for j in range(self.data['c']):
                    kkk = mat_k[i][j]
                    sss = mat_s[i][j]
                    ccc = [kkk, sss]
                    try:
                        if combinat.index(ccc):
                            self.data['mat_inf_index'][i][j] = combinat.index(ccc)
                    except:
                        combinat.append(ccc)
                        self.data['combinatIndex'].append(
                            [combinat.index(ccc), kkk, sss, 0]
                        )
                        self.data['mat_inf_index'][i][j] = combinat.index(
                            ccc
                        )

        # vyrezani krajnich bunek, kde byly chyby, je to vyrazeno u
        # sklonu a acc
        i = j = 0

        # data value vector intersection
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                x_mat_dem = self.data['mat_dem'][i][j]
                slp = self.data['mat_slope'][i][j]
                if x_mat_dem == self.data['NoDataValue'] or \
                   slp == self.data['NoDataValue']:
                    self.data['mat_nan'][i][j] = self.data['NoDataValue']
                    self.data['mat_slope'][i][j] = self.data['NoDataValue']
                    self.data['mat_dem'][i][j] = self.data['NoDataValue']
                else:
                    self.data['mat_nan'][i][j] = 0

        ### TODO
        ### self._save_raster("mat_nan", self.data['mat_nan'], self.data['temp'])

        return all_attrib

    def _get_array_points(self):
        raise NotImplemented("Not implemented for base provider")

    def _get_array_points_(self, x, y, fid, i):
        """Internal method called by _get_array_points().
        """
        # position i,j in raster (starts at 0)
        r = int(self.data['r'] - ((y - self.data['yllcorner']) // self.data['vpix']) - 1)
        c = int((x - self.data['xllcorner']) // self.data['spix'])

        # if point is not on the edge of raster or its
        # neighbours are not "NoDataValue", it will be saved
        # into array_points array
        if r != 0 and r != self.data['r'] \
           and c != 0 and c != self.data['c'] and \
           self.data['mat_dem'][r][c] != self.data['NoDataValue'] and \
           self.data['mat_dem'][r-1][c] != self.data['NoDataValue'] and \
           self.data['mat_dem'][r+1][c] != self.data['NoDataValue'] and \
           self.data['mat_dem'][r][c-1] != self.data['NoDataValue'] and \
           self.data['mat_dem'][r][c+1] != self.data['NoDataValue']:

            self.data['array_points'][i][0] = fid
            self.data['array_points'][i][1] = r
            self.data['array_points'][i][2] = c
            # x,y coordinates of current point stored in an array
            self.data['array_points'][i][3] = x
            self.data['array_points'][i][4] = y
        else:
            Logger.info(
                "Point FID = {} is at the edge of the raster."
                "This point will not be included in results.".format(
                    fid
            ))

        return i

    def _get_a(self, all_attrib):
        """
        Build 'a' array.

        :param all_attrib: list of attributes (numpy arrays)
        """
        mat_n = all_attrib[2]
        mat_x = all_attrib[7]
        mat_y = all_attrib[8]
        
        self.data['mat_a']  = np.zeros(
            [self.data['r'], self.data['c']], float
        )
        self.data['mat_aa'] = np.zeros(
            [self.data['r'], self.data['c']], float
        )

        # calculating the "a" parameter
        for i in range(self.data['r']):
            for j in range(self.data['c']):
                slope = self.data['mat_slope'][i][j]
                par_x = mat_x[i][j]
                par_y = mat_y[i][j]

                if par_x == self.data['NoDataValue'] or \
                   par_y == self.data['NoDataValue'] or \
                   slope == self.data['NoDataValue']:
                    par_a = self.data['NoDataValue']
                    par_aa = self.data['NoDataValue']
                elif par_x == self.data['NoDataValue'] or \
                     par_y == self.data['NoDataValue'] or \
                     slope == 0.0:
                    par_a = 0.0001
                    par_aa = par_a / 100 / mat_n[i][j]
                else:
                    exp = np.power(slope, par_y)
                    par_a = par_x * exp
                    par_aa = par_a / 100 / mat_n[i][j]

                self.data['mat_a'][i][j] = par_a
                self.data['mat_aa'][i][j] = par_aa

    def _get_crit_water(self, all_attrib):
        """

        :param all_attrib:
        """

        mat_b = all_attrib[6]
        mat_tau = all_attrib[9]
        mat_v = all_attrib[10]

        # critical water level
        mat_hcrit_tau = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_v = np.zeros([self.data['r'], self.data['c']], float)
        mat_hcrit_flux = np.zeros([self.data['r'], self.data['c']], float)
        self.data['mat_hcrit'] = np.zeros([self.data['r'], self.data['c']], float)

        for i in range(self.data['r']):
            for j in range(self.data['c']):
                if self.data['mat_slope'][i][j] != self.data['NoDataValue'] \
                   and mat_tau[i][j] != self.data['NoDataValue']:
                    slope = self.data['mat_slope'][i][j]
                    tau_crit = mat_tau[i][j]
                    v_crit = mat_v[i][j]
                    b = mat_b[i][j]
                    aa = self.data['mat_aa'][i][j]
                    flux_crit = tau_crit * v_crit
                    exp = 1 / (b - 1)

                    if slope == 0.0:
                        hcrit_tau = hcrit_v = hcrit_flux = 1000

                    else:
                        hcrit_v = np.power((v_crit / aa), exp)  # h critical from v
                        hcrit_tau = tau_crit / 98.07 / slope  # h critical from tau
                        hcrit_flux = np.power((flux_crit / slope / 98.07 / aa),(1 / mat_b[i][j]))  # kontrola jednotek

                    mat_hcrit_tau[i][j] = hcrit_tau
                    mat_hcrit_v[i][j] = hcrit_v
                    mat_hcrit_flux[i][j] = hcrit_flux
                    hcrit = min(hcrit_tau, hcrit_v, hcrit_flux)
                    self.data['mat_hcrit'][i][j] = hcrit
                else:
                    mat_hcrit_tau[i][j] = self.data['NoDataValue']
                    mat_hcrit_v[i][j] = self.data['NoDataValue']
                    mat_hcrit_flux[i][j] = self.data['NoDataValue']
                    self.data['mat_hcrit'][i][j] = self.data['NoDataValue']

        # TODO
        # self._save_raster("hcrit_tau", mat_hcrit_tau)
        # self._save_raster("hcrit_flux", mat_hcrit_flux)
        # self._save_raster("hcrit_v", mat_hcrit_v)

    def _get_slope_dir(self, dem_clip):
        raise NotImplemented("Not implemented for base provider")

    def _prepare_streams(self, mask_shp, dem_clip, intersect):
        """

        :param mask_shp:
        :param dem_clip:
        :param intersect:
        """
        self.data['type_of_computing'] = 1

        # pocitam vzdy s ryhama pokud jsou zadane vsechny vstupy pro
        # vypocet toku, toky se pocitaji a type_of_computing je 3
        listin = [self._input_params['stream'],
                  self._input_params['table_stream_shape'],
                  self._input_params['table_stream_shape_code']]
        tflistin = [len(i) > 1 for i in listin] ### TODO: ???

        if all(tflistin):
            self.data['type_of_computing'] = 3

        if self.data['type_of_computing'] in (3, 5):
            args = [
                self._input_params['stream'],
                self._input_params['table_stream_shape'],
                self._input_params['table_stream_shape_code'],
                self._input_params['elevation'],
                mask_shp,
                self.data['spix'],
                self.data['r'],
                self.data['c'],
                (self.data['xllcorner'], self.data['yllcorner']),
                self.data['outdir'],
                dem_clip,
                intersect,
                self._primary_key
            ]

            self.data['toky'], self.data['mat_tok_reach'], self.data['toky_loc'] = \
                self._streamPreparation(args)
        else:
            self.data['toky'] = None
            self.data['mat_tok_reach'] = None
            self.data['toky_loc'] = None

    def _find_boundary_cells(self):
        """
        ? TODO: is it used?
        """
        # Identification of cells at the domain boundary

        self.data['mat_boundary'] = np.zeros(
            [self.data['r'], self.data['c']], float
        )

        nr = range(self.data['r'])
        nc = range(self.data['c'])

        self.data['rc'] = []
        self.data['rr'] = []

        for i in nr:
            for j in nc:
                val = self.data['mat_nan'][i][j]
                if i == 0 or j == 0 or \
                   i == (self.data['r'] - 1) or j == (self.data['c'] - 1):
                    if val != self.data['NoDataValue']:
                        val = -99
                else:
                    if val != self.data['NoDataValue']:
                        if  self.data['mat_nan'][i - 1][j] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i][j - 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i][j - 1] == self.data['NoDataValue']:

                            val = -99

                        if  self.data['mat_nan'][i - 1][j + 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j + 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i - 1][j - 1] == self.data['NoDataValue'] or \
                            self.data['mat_nan'][i + 1][j - 1] == self.data['NoDataValue']:

                            val = -99.

                self.data['mat_boundary'][i][j] = val

        inDomain = False
        inBoundary = False

        for i in nr:
            oneCol = []
            oneColBoundary = []
            for j in nc:

                if self.data['mat_boundary'][i][j] == -99 and inBoundary == False:
                    inBoundary = True

                if self.data['mat_boundary'][i][j] == -99 and inBoundary:
                    oneColBoundary.append(j)

                if (self.data['mat_boundary'][i][j] == 0.0) and inDomain == False:
                    self.data['rr'].append(i)
                    inDomain = True

                if (self.data['mat_boundary'][i][j] == 0.0) and inDomain:
                    oneCol.append(j)

            inDomain = False
            inBoundary = False
            self.data['rc'].append(oneCol)

    def _clip_data(self, dem, intersect, slope, flow_direction):
        raise NotImplemented("Not implemented for base provider")

    @staticmethod
    def _diff_npoints(npoints1, npoints2):
        diffpts = npoints1 - npoints2
        if diffpts > 0:
            Logger.warning(
                "{} points outside of computation domain "
                "will be ignored".format(diffpts)
            )

    @staticmethod
    def _streamPreparation(args):
        raise NotImplemented("Not implemented for base provider")
