class PrepareDataBase(object):
    def run(self):
        Logger.info("DATA PREPARATION")
        Logger.info("----------------")

        self._create_dict()

        # get input parameters from GRASS UI
        # TODO: TBD

        # set dict parameters from input data (fixed)
        # TODO: code duplication
        self.data['maxdt'] = maxdt
        self.data['end_time'] = end_time
        self.data['outdir'] = output
        self.data['points'] = points

        # create output folder, where temporary data are stored
        # TODO: code duplication
        self._add_message("Creating output...")
        self._set_output() 
        self._set_mask()   #  TODO

        Logger.info(
            "Computing fill, flow direction, flow accumulation, slope..."
        )
        dmt_fill, flow_direction, flow_accumulation, slope_orig = \
            dmtfce(dmt_copy, self.data['temp'], "NONE") # TODO

        # intersect
        Logger.info("Computing intersect of input data...")
        intersect, null_shp, sfield = self._get_intersect(
            gp, dmt_copy, veg_indata, soil_indata, vtyp, ptyp,
            tab_puda_veg, tab_puda_veg_code
        )

        # clip
        Logger.info("Clip of the source data by intersect...")
        flow_direction_clip, slope_clip, dmt_clip = self._clip_data(
            dmt_copy, intersect, slope_orig, flow_direction
        )

        Logger.info("Computing parameters of DMT...")
        # raster to numpy array conversion
        self.data['mat_dmt'] = self._rst2np(dmt_clip)
        self.data['mat_slope'] = self._rst2np(slope_clip)
        self.data['mat_fd'] = self._rst2np(flow_direction_clip)

        ll_corner = self._get_raster_dim(dmt_clip)

        all_attrib = self._get_mat_par(sfield, intersect)

        self._get_array_points(gp)

        self._get_a(all_attrib)

        self._get_crit_water(all_attrib, ll_corner)

        # load precipitation input file
        self.data['sr'], self.data['itera'] = \
            rainfall.load_precipitation(rainfall_file_path)

        # compute aspect
        self._get_slope_dir(dmt_clip)

        Logger.info("Computing stream preparation...")
        self._prepare_streams(stream, tab_stream_tvar, tab_stream_tvar_code,
                              dmt, null_shp, ll_corner, dmt_clip, intersect
        )
        
        self._find_boundary_cells()

        self._save_raster("fl_dir", self.data['mat_fd'], self.data['temp'])

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

        return self.data

    def _create_dict(self):
        """
        Creates dictionary to which model parameters are computed.
        """

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
            'maxdt': None,
            'mat_pi': None,
            'mat_ppl': None,
            'surface_retention': None,
            'mat_inf_index': None,
            'mat_hcrit': None,
            'mat_aa': None,
            'mat_b': None,
            'mat_reten': None,
            'mat_fd': None,
            'mat_dmt': None,
            'mat_efect_vrst': None,
            'mat_slope': None,
            'mat_nan': None,
            'mat_a': None,
            'mat_n': None,
            'outdir': None,
            'pixel_area': None,
            'points': None,
            'poradi': None,
            'end_time': None,
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
    
