import os
import sys
import argparse
import logging
import numpy as np
if sys.version_info.major >= 3:
    from configparser import ConfigParser, NoSectionError
else:
    from ConfigParser import ConfigParser, NoSectionError

from smoderp2d.core.general import Globals
import math
from smoderp2d.providers.base import BaseProvider, Logger, CompType, BaseWritter
from smoderp2d.exceptions import ConfigError, ProviderError

class CmdWritter(BaseWritter):
    def __init__(self):
        super(CmdWritter, self).__init__()

    def write_raster(self, array, output_name, directory='core'):
        """Write raster (numpy array) to ASCII file.

        :param array: numpy array
        :param output_name: output filename
        :param directory: directory where to write output file
        """
        file_output = self._raster_output_path(output_name, directory)

        np.savetxt(file_output, array, fmt='%.6e')

        self._print_array_stats(
            array, file_output
        )

class NoGisProvider(BaseProvider):
    def __init__(self):
        """Create argument parser."""
        super(NoGisProvider, self).__init__()

        # define CLI parser
        parser = argparse.ArgumentParser(description='Run NoGis Smoderp2D.')

        # data file (only required for runoff)
        parser.add_argument(
            '-cfg',
            help='file with configuration',
            type=str
        )

        self.args = parser.parse_args()

        # no gis has only roff comp type
        self.args.typecomp = 'roff'
        self.args.typecomp = CompType()[self.args.typecomp]

        # load configuration
        self._config = ConfigParser()
        if self.args.typecomp == CompType.roff:
            if not self.args.cfg:
                parser.error('-cfg required')
            if not os.path.exists(self.args.cfg):
                raise ConfigError("{} does not exist".format(
                    self.args.cfg
                ))
            self._config.read(self.args.cfg)

        try:
            # set logging level
            Logger.setLevel(self._config.get('general', 'logging'))
            # sys.stderr logging
            self._add_logging_handler(
                logging.StreamHandler(stream=sys.stderr)
            )

            # must be defined for _cleanup() method
            Globals.outdir = self._config.get('general', 'outdir')
        except NoSectionError as e:
            raise ConfigError('Config file {}: {}'.format(
                self.args.cfg, e
            ))

        # define storage writter
        self.storage = CmdWritter()

    @staticmethod
    def _load_csv_data(filename):
        """Get data from a CSV file in a dict-like form.

        :param filename: Path to the CSV file
        :return: ndarray queryable as a dict (key_vals = data['key'])
        """
        return np.genfromtxt(filename, delimiter=';', names=True, dtype=None,
                             encoding='utf-8-sig', deletechars='')

    def _load_nogis(self, filename_indata, filename_soil_types):
        """Load configuration data from roff computation procedure.

        :param str filename_indata: input CSV file
        :param str filename_soil_types: soil types CSV file

        :return dict: loaded data
        """
        from smoderp2d.processes import rainfall

        # TODO
        # read input csv files
        try:
            data = self._load_data(filename_indata)
            # TODO
            # indata = self._load_csv_data(filename_indata)
            # soil_types = self._load_csv_data(filename_soil_types)
            # data = self._table_join(indata, soil_types)
        except IOError as e:
            raise ProviderError('{}'.format(e))

        # defaults for nogis provider
        #  type of computing =  1 sheet and rill flow
        data['type_of_computing'] = 1
        data['mfda'] = False

        # time settings
        data['end_time'] = self._config.getfloat('time', 'endtime') * 60.0
        data['maxdt'] = self._config.getfloat('time', 'maxdt')

        # load precipitation input file
        try:
            data['sr'], data['itera'] = rainfall.load_precipitation(
                self._config.get('rainfall', 'file')
            )
        except TypeError:
            raise ProviderError('Invalid file in [rainfall] section')

        # general settings
        # output directory is always set
        data['outdir'] = self._config.get('general', 'outdir')
        data['temp'] = os.path.join(data['outdir'], 'temp')
        # some self._configs are not in pickle.dump
        data['extraOut'] = self._config.getboolean('general', 'extraout')
        # rainfall data can be saved
        data['prtTimes'] = self._config.get('general', 'printtimes')

        resolution = self._config.getfloat('domain', 'res')
        # TODO: Uncomment and comment the latter when trying with real
        #  input CSV and not the .save file
        # TODO: Change stah -> svah (ha ha) after being changed in the CSV
        # data['r'] = self._compute_rows(indata['vodorovny_prumet_stahu[m]'],
        #                                resolution)
        data['r'] = 10
        data['c'] = 1
        # set mask i and j must be set after 'r' and 'c'
        data['rr'], data['rc'] = self._construct_rr_rc(data)

        # set cell sizes
        data['vpix'] = data['spix'] = self._config.getfloat('domain', 'res')
        data['pixel_area'] = data['vpix'] * data['spix']

        # allocate matrices
        self._alloc_matrices(data)

        # topography
        # TODO: load from csv - 1) hor. length + height 2) hor. length + ratio
        # same cell values for each segment
        data['mat_slope'].fill(self._config.getfloat('topography', 'slope'))
        # TODO can mat boundary stay zero?
        # data['mat_boundary'] = np.zeros((data['r'],data['c']), float)
        data['mat_efect_cont'] = data['spix'] # x-axis (EW) resolution
        # flow direction is always to the south
        data['mat_fd'].fill(4)

        # set values to parameter matrics
        # TODO: See providers/base/data_preparation._get_a()
        # TODO: See providers/base/data_preparation._get_crit_water()
        data['mat_b'].fill(self._config.getfloat('parameters', 'b')) # soil types
        data['mat_a'].fill(self._config.getfloat('parameters', 'X'))
        data['mat_n'].fill(self._config.getfloat('parameters', 'n'))
        data['mat_hcrit'].fill(self._config.getfloat('parameters', 'hcrit'))
        data['mat_aa'] = data['mat_a']*data['mat_slope']**(
            self._config.getfloat('parameters','Y')
            )
        # retention is converted from mm to m in _set_globals function
        # TODO: See join table
        data['mat_reten'].fill(self._config.getfloat('parameters', 'ret'))
        data['mat_pi'].fill(self._config.getfloat('parameters', 'pi'))
        data['mat_ppl'].fill(self._config.getfloat('parameters', 'ppl'))

        data['mat_nan'] = np.nan
        data['mat_inf_index'].fill(1)  # 1 = philips infiltration

        # QUESTION: TODO set infiltration values
        # needs to be constructed from input data
        self._set_combinatIndex(data)

        # QUESTION: TODO set points to hydrographs
        self._set_hydrographs(data)

        # set no data value, likely used in nogis provider
        data['NoDataValue'] = -9999
        # and other unused variables
        self._set_unused(data)

        return data

    @staticmethod
    def _compute_rows(lengths, resolution):
        """Compute number of pixels the slope will be divided into.

        :param lengths: np array with containing all lengths
        :param resolution: intended resolution of one pixel
        :return: number of pixels
        """
        length = lengths.sum()
        # TODO: Change the horizonthal length to the one with the slope
        nr_of_rows = round(length / resolution)

        return nr_of_rows

    def _alloc_matrices(self, data):
        # TODO: use loop (check base provider)
        # allocate matrices
        data['mat_b'] = np.zeros((data['r'],data['c']), float)
        data['mat_stream_reach'] = np.zeros((data['r'],data['c']), float)
        data['mat_a'] = np.zeros((data['r'],data['c']), float)
        data['mat_slope'] = np.zeros((data['r'],data['c']), float)
        data['mat_n'] = np.zeros((data['r'],data['c']), float)
        # dem is not needed for computation
        # data['mat_dem'] = np.zeros((data['r'],data['c']), float)
        data['mat_inf_index'] = np.zeros((data['r'],data['c']), float)
        data['mat_fd'] = np.zeros((data['r'],data['c']), float)
        data['mat_hcrit'] = np.zeros((data['r'],data['c']), float)
        data['mat_aa'] = np.zeros((data['r'],data['c']), float)
        data['mat_reten'] = np.zeros((data['r'],data['c']), float)
        data['mat_nan'] = np.zeros((data['r'],data['c']), float)
        data['mat_efect_cont'] = np.zeros((data['r'],data['c']), float)
        data['mat_pi'] = np.zeros((data['r'],data['c']), float)
        data['mat_boundary'] = np.zeros((data['r'],data['c']), float)
        data['mat_ppl'] = np.zeros((data['r'],data['c']), float)

    def _construct_rr_rc(self, data):
        """Create list rr and list of lists rc which contain i and j index of
        elements inside the compuation domain.

        :return: rr, rc
        """

        rr = range(data['r'])
        rc = [range(data['c'])]*data['r']

        return rr, rc


    def _set_combinatIndex(self, data):
        # TODO: See providers/base/data_preparation._get_mat_par()
        pass

    def _set_unused(self, data):
        data['cell_stream'] = None
        data['state_cell'] = None
        data['outletCells'] = None
        data['STREAM_RATIO'] = None
        data['bc'] = None
        data['br'] = None
        data['streams_loc'] = None
        data['streams'] = None
        data['poradi'] = None
        data['points'] = None

    def _set_hydrographs(self, data):
        # TODO: so far not needed
        # TODO: do only in the lowest point
        pass

    def load(self):
        """Load configuration data.
        from the config data

        Only roff procedure supported.
        """

        # cleanup output directory first
        self._cleanup()

        data = self._load_nogis(
            self._config.get('Other', 'indata'),
            # TODO
            # self._config.get('Other', 'data1d'),
            self._config.get('Other', 'data1d_soil_types'),
        )

        #TODO
        print ('')
        print ('')
        print ('NO GIS PROVIDER')
        print ('')
        for key in data:
            print(key)
        print ('')
        print ('in progress stop in {}'.format(os.path.join(os.path.dirname(__file__))))
        print ('next step: make poirts to print hydrograms, set combinatIndex  and set cell sizes')

        self._set_globals(data)
        # sys.exit()
