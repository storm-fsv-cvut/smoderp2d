from __future__ import print_function

import os
import sys
import shutil
import math
import pickle
import logging
import numpy as np

from smoderp2d.providers import Logger
from smoderp2d.providers.base.exceptions import DataPreparationError
from smoderp2d.core.general import GridGlobals, DataGlobals, Globals
from smoderp2d.exceptions import ProviderError

class Args:
    # type of computation (CompType)
    typecomp = None
    # path to data file (used by 'dpre' for output and 'roff' for
    # input)
    data_file = None

# unfortunately Python version shipped by ArcGIS 10 lacks Enum
class CompType:
    # type of computation
    dpre = 0
    roff = 1
    full = 2

    @classmethod
    def __getitem__(cls, key):
        if key == 'dpre':
            return cls.dpre
        elif key == 'roff':
            return cls.roff
        else:
            return cls.full

class BaseProvider(object):
    def __init__(self):
        self.args = Args()

        self._print_fn = print
        self._print_logo_fn = print

        # default logging level (can be modified by provider)
        Logger.setLevel(logging.DEBUG)

    @staticmethod
    def _add_logging_handler(handler, formatter=None):
        """Register new logging handler.
        
        :param handler: loggging handler to be registerered
        :param formatter: logging handler formatting
        """
        if not formatter:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(module)s:%(lineno)s]"
            )
        handler.setFormatter(formatter)
        Logger.addHandler(handler)

    def _load_dpre(self):
        """Run data preparation procedure.

        See ArcGisProvider and GrassGisProvider for implementation issues.

        :return dict: loaded data
        """
        raise NotImplementedError()

    def _load_roff(self, indata):
        """Load configuration data from roff computation procedure.

        :param str indata: configuration filename

        :return dict: loaded data
        """
        from smoderp2d.processes import rainfall

        # the data are loared from a pickle file
        try:
            data = self._load_data(indata)
            if isinstance(data, list):
                raise ProviderError(
                    'Saved data out-dated. Please use '
                    'utils/convert-saved-data.py for update.'
                )
        except IOError as e:
            raise ProviderError('{}'.format(e))

        # some variables configs can be changes after loading from
        # pickle.dump such as end time of simulation

        if self._config.get('time', 'endtime') != '-':
            data['end_time'] = self._config.getfloat('time', 'endtime') * 60.0

        #  time of flow algorithm
        if self._config.get('Other', 'mfda') != '-':
            data['mfda'] = self._config.getboolean('Other', 'mfda')

        #  type of computing:
        #    0 sheet only,
        #    1 sheet and rill flow,
        #    2 sheet and subsurface flow,
        #    3 sheet, rill and reach flow
        if self._config.get('Other', 'typecomp') != '-':
            data['type_of_computing'] = self._config.get('Other', 'typecomp')

        #  output directory is always set
        data['outdir'] = self._config.get('Other', 'outdir')

        #  rainfall data can be saved
        if self._config.get('srazka', 'file') != '-':
            try:
                data['sr'], data['itera'] = rainfall.load_precipitation(
                    self._config.get('srazka', 'file')
                )
            except TypeError:
                raise ProviderError('Invalid file in [srazka] section')

        # some self._configs are not in pickle.dump
        data['extraOut'] = self._config.getboolean('Other', 'extraout')
        # rainfall data can be saved
        data['prtTimes'] = self._config.get('Other', 'printtimes')

        data['maxdt'] = self._config.getfloat('time', 'maxdt')

        return data

    def load(self):
        """Load configuration data."""
        if self.args.typecomp not in (CompType.dpre, CompType.roff, CompType.full):
            raise ProviderError('Unsupported partial computing: {}'.format(
                self.args.typecomp
            ))

        # cleanup output directory first
        self._cleanup()

        data = None
        if self.args.typecomp in (CompType.dpre, CompType.full):
            try:
                data = self._load_dpre()
            except DataPreparationError as e:
                raise ProviderError('{}'.format(e))
            if self.args.typecomp == CompType.dpre:
                # data preparation requested only
                self._save_data(data, self.args.data_file)
                return

        if self.args.typecomp == CompType.roff:
            data = self._load_roff(self.args.data_file)

        # roff || full
        self._set_globals(data)

    def _set_globals(self, data):
        """Set global variables.

        :param dict data: data to be set
        """
        for item in data.keys():
            if hasattr(Globals, item):
                setattr(Globals, item, data[item])
            elif hasattr(GridGlobals, item):
                setattr(GridGlobals, item, data[item])
            elif hasattr(DataGlobals, item):
                setattr(DataGlobals, item, data[item])

        GridGlobals.NoDataInt = int(-9999)
        GridGlobals.dx = math.sqrt(data['pixel_area'])
        GridGlobals.dy = GridGlobals.dx
        Globals.mat_reten = -1.0 * data['mat_reten'] / 1000
        Globals.diffuse = self._comp_type(data['type_of_computing'])['diffuse']
        Globals.subflow = self._comp_type(data['type_of_computing'])['subflow']
        # TODO: lines below are part only of linux method
        Globals.isRill = self._comp_type(data['type_of_computing'])['rill']
        Globals.isStream = self._comp_type(data['type_of_computing'])['stream']
        Globals.prtTimes = data.get('prtTimes', None)

    @staticmethod
    def _cleanup():
        """Clean-up output directory.

        :param output_dir: output directory to clean up
        """
        output_dir = Globals.outdir
        if not output_dir:
            # no output directory defined
            return
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
    @staticmethod
    def _comp_type(tc):
        """Returns boolean information about the components of the computation.
        
        Return 4 true/values for rill, subflow, stream, diffuse
        presence/non-presence.

        :param str tc: type of computation

        :return dict:
        """
        ret = {}
        for item in ('diffuse',
                     'subflow',
                     'stream',
                     'rill',
                     'only_surface'):
            ret[item] = False

        itc = int(tc)
        if itc == 1:
            ret['rill'] = True
        elif itc == 3:
            ret['stream'] = True
            ret['rill'] = True
        elif itc == 4:
            ret['subflow'] = True
            ret['rill'] = True
        elif itc == 5:
            ret['stream'] = True
            ret['subflow'] = True
            ret['rill'] = True
        elif itc == 0:
            ret['only_surface'] = True

        return ret

    def logo(self):
        """Print Smoderp2d ascii-style logo."""
        logo_file = os.path.join(os.path.dirname(__file__), 'txtlogo.txt')
        with open(logo_file, 'r') as fd:
            self._print_logo_fn(fd.read())
        self._print_logo_fn('') # extra line

    @staticmethod
    def _save_data(data, filename):
        """Save data into pickle.
        """
        if filename is None:
            raise ProviderError('Output file for saving data not defined')
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename, 'wb') as fd:
            pickle.dump(data, fd, protocol=2)
        Logger.info('Pickle file created in <{}> ({} bytes)'.format(
            filename, sys.getsizeof(data)
        ))

    @staticmethod
    def _load_data(filename):
        """Load data from pickle.

        :param str filename: file to be loaded
        """
        if filename is None:
            raise ProviderError('Input file for loading data not defined')
        with open(filename, 'rb') as fd:
            if sys.version_info > (3, 0):
                data = pickle.load(fd, encoding='bytes')
                data = {
                    key.decode(): val.decode if isinstance(val, bytes) else val for key, val in data.items()
                }
            else:
                data = pickle.load(fd)
        Logger.debug('Size of loaded data is {} bytes'.format(
            sys.getsizeof(data))
        )

        return data

    def postprocessing(self, cumulative, surface_array):
        rrows = GridGlobals.rr
        rcols = GridGlobals.rc

        for i in rrows:
            for j in rcols[i]:
                if cumulative.h_sur_tot[i][j] == 0.:
                    cumulative.v_sheet[i][j] = 0.
                else:
                    cumulative.v_sheet[i][j] = \
                        cumulative.q_sheet[i][j] / cumulative.h_sur_tot[i][j]
                cumulative.shear_sheet[i][j] = \
                    cumulative.h_sur_tot[i][j] * 98.07 * Globals.mat_slope[i][j]

        # define output data to be produced
        data_output = [
            'infiltration',
            'precipitation',
            'v_sheet',
            'shear_sheet',
            'q_sur_tot',
            'vol_sur_tot'
        ]
        if Globals.subflow:
            data_output += [
                'vol_sur_r',
                'q_sur_tot',  # TODO: twice ?
                'vol_sur_tot' # TODO: twice ?
            ]
            # 17, 18]
        if Globals.extraOut:
            data_output += [
                'q_sheet',
                'h_rill',
                'q_rill',
                'b_rill',
                'inflow_sur',
                'sur_ret',
                'vol_sur_r'  # TODO: twice ?
            ]
        # avoid duplicates
        data_output = list(set(data_output))

        finState = np.zeros(np.shape(surface_array), int)
        finState.fill(GridGlobals.NoDataValue) # TODO: int ?
        vRest = np.zeros(np.shape(surface_array), float)
        vRest.fill(GridGlobals.NoDataValue)
        totalBil = cumulative.infiltration.copy()
        totalBil.fill(0.0)

        for i in rrows:
            for j in rcols[i]:
                finState[i][j] = int(surface_array[i][j].state)

        # make rasters from cumulative class
        for item in data_output:
            self._raster_output(
                getattr(cumulative, item),
                cumulative.data[item].file_name
            )

        for i in rrows:
            for j in rcols[i]:
                if finState[i][j] >= 1000:
                    vRest[i][j] = GridGlobals.NoDataValue
                else:
                    vRest[i][j] = surface_array[i][j].h_total_new * GridGlobals.pixel_area

        totalBil = (cumulative.precipitation + cumulative.inflow_sur) - \
            (cumulative.infiltration + cumulative.vol_sur_r + cumulative.vol_rill) - \
            cumulative.sur_ret  # + (cumulative.v_sur_r + cumulative.v_rill_r)
        totalBil -= vRest

        self._raster_output(totalBil, 'massBalance')
        self._raster_output(finState, 'reachFid')
        self._raster_output(vRest, 'volRest_m3')

        # TODO
        # if not Globals.extraOut:
        #     if os.path.exists(output + os.sep + 'temp'):
        #         shutil.rmtree(output + os.sep + 'temp')
        #     if os.path.exists(output + os.sep + 'temp_dp'):
        #         shutil.rmtree(output + os.sep + 'temp_dp')
        #     return 1


    @staticmethod
    def _raster_output_path(output):
        return os.path.join(
            Globals.outdir,
            output + '.asc'
        )
 
    def _raster_output(self, arr, output):
        """Write raster to ASCII file.

        :param arr: numpy array
        :param output: output filename
        """
        raise NotImplementedError()
