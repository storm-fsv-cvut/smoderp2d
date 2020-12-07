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

class BaseWritter(object):
    def __init__(self):
        self.primary_key = None

    @staticmethod
    def _raster_output_path(output, directory=''):
        dir_name = os.path.join(
            Globals.outdir,
            directory
            )

        if not os.path.exists(dir_name):
           os.makedirs(dir_name)

        return os.path.join(
            dir_name,
            output + '.asc'
        )

    @staticmethod
    def _print_array_stats(arr, file_output):
        """Print array stats.
        """

        Logger.info("Raster ASCII output file {} saved".format(
            file_output
        ))
        Logger.info("\tArray stats: min={} max={} mean={}".format(
            np.min(arr), np.max(arr), np.mean(arr)
        ))

    # todo: abstractmethod
    def write_raster(self, arr, output):
        pass

class BaseProvider(object):
    def __init__(self):
        self.args = Args()

        self._print_fn = print
        self._print_logo_fn = print

        # default logging level (can be modified by provider)
        Logger.setLevel(logging.DEBUG)

        # storage writter must be defined
        self.storage = None

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
        if data['outdir'] is None:
            data['outdir'] = self._config.get('Other', 'outdir')

        #  rainfall data can be saved
        if self._config.get('rainfall', 'file') != '-':
            try:
                data['sr'], data['itera'] = rainfall.load_precipitation(
                    self._config.get('rainfall', 'file')
                )
            except TypeError:
                raise ProviderError('Invalid file in [rainfall] section')

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
                if getattr(Globals, item) is None:
                    setattr(Globals, item, data[item])
            elif hasattr(GridGlobals, item):
                setattr(GridGlobals, item, data[item])
            elif hasattr(DataGlobals, item):
                setattr(DataGlobals, item, data[item])

        GridGlobals.NoDataInt = int(-9999)
        Globals.mat_reten = -1.0 * data['mat_reten'] / 1000
        Globals.diffuse = self._comp_type(data['type_of_computing'])['diffuse']
        Globals.subflow = self._comp_type(data['type_of_computing'])['subflow']
        # TODO: 2 lines bellow are duplicated for arcgis provider. fist
        # definition of dx dy is in
        # (provider.arcgis.data_prepraration._get_raster_dim) where is is
        # defined for write_raster which is used before _set_globals
        GridGlobals.dx = math.sqrt(data['pixel_area'])
        GridGlobals.dy = GridGlobals.dx
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

    def postprocessing(self, cumulative, surface_array, stream):

        rrows = GridGlobals.rr
        rcols = GridGlobals.rc

        # compute maximum shear stress
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

        # extra outputs from cumulative class are printed by
        # default to temp dir
        # if Globals.extraOut:
        data_output_extras = [
                'h_sur_tot',
                'q_sheet',
                'vol_sheet',
                'h_rill',
                'q_rill',
                'vol_rill',
                'b_rill',
                'inflow_sur',
                'sur_ret',
                'vol_sur_r' 
        ]

        if Globals.subflow:
            # Not implemented yet
            pass
            # data_output += [
            # ]

        # make rasters from cumulative class
        for item in data_output:
            self.storage.write_raster(
                self._make_mask(getattr(cumulative, item)),
                cumulative.data[item].file_name
            )

        # make extra rasters from cumulative clasess into temp dir 
        for item in data_output_extras:
            self.storage.write_raster(
                self._make_mask(getattr(cumulative, item)),
                cumulative.data[item].file_name,
                directory=cumulative.data[item].data_type
            )

        finState = np.zeros(np.shape(surface_array), int)
        finState.fill(GridGlobals.NoDataInt)
        vRest = np.zeros(np.shape(surface_array), float)
        vRest.fill(GridGlobals.NoDataValue)
        totalBil = cumulative.infiltration.copy()
        totalBil.fill(0.0)

        for i in rrows:
            for j in rcols[i]:
                finState[i][j] = int(surface_array[i][j].state)
                if finState[i][j] >= 1000:
                    vRest[i][j] = GridGlobals.NoDataValue
                else:
                    vRest[i][j] = surface_array[i][j].h_total_new * GridGlobals.pixel_area 

        totalBil = (cumulative.precipitation + cumulative.inflow_sur) - \
            (cumulative.infiltration + cumulative.vol_sur_tot) - \
            cumulative.sur_ret - vRest

        for i in rrows:
            for j in rcols[i]:
                if  int(surface_array[i][j].state) >= 1000 :
                    totalBil[i][j] = GridGlobals.NoDataValue

        self.storage.write_raster(self._make_mask(totalBil), 'massBalance')
        self.storage.write_raster(self._make_mask(vRest), 'volRest_m3')
        self.storage.write_raster(self._make_mask(finState, int_=True),
                'reachFid')

        # store stream reaches results to a table
        # if stream is calculated
        if stream:
            n = len(stream)
            m = 7
            outputtable = np.zeros([n,m])
            fid = list(stream.keys())
            for i in range(n):
                outputtable[i][0] = stream[fid[i]].fid
                outputtable[i][1] = stream[fid[i]].b
                outputtable[i][2] = stream[fid[i]].m
                outputtable[i][3] = stream[fid[i]].roughness
                outputtable[i][4] = stream[fid[i]].q365
                outputtable[i][5] = stream[fid[i]].V_out_cum
                outputtable[i][6] = stream[fid[i]].Q_max
            
            path_ = os.path.join(
                    Globals.outdir,
                    'stream.csv'
                    )
            np.savetxt(path_, outputtable, delimiter=';',fmt = '%.3e',
                       header='FID{sep}b_m{sep}m__{sep}rough_s_m1_3{sep}q365_m3_s{sep}V_out_cum_m3{sep}Q_max_m3_s'.format(sep=';'))


    def _make_mask(self, arr, int_=False):
        """ Assure that the no data value is outside the 
        computation region.
        Works only for type float.
        
        :param arrr: numpy array
        """

        rrows = GridGlobals.rr
        rcols = GridGlobals.rc

        copy_arr = arr.copy()
        if (int_) :
            arr.fill(GridGlobals.NoDataInt)
        else:
            arr.fill(GridGlobals.NoDataValue)

        for i in rrows:
            for j in rcols[i]:
                arr[i][j] = copy_arr[i][j]

        return arr


        # TODO
        # if not Globals.extraOut:
        #     if os.path.exists(output + os.sep + 'temp'):
        #         shutil.rmtree(output + os.sep + 'temp')
        #     if os.path.exists(output + os.sep + 'temp_dp'):
        #         shutil.rmtree(output + os.sep + 'temp_dp')
        #     return 1
