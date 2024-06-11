from __future__ import print_function

import os
import sys
import shutil
import math
import pickle
import logging
import numpy as np
import numpy.ma as ma
from configparser import ConfigParser, NoSectionError, NoOptionError
from abc import abstractmethod

from smoderp2d.core import CompType
from smoderp2d.core.general import GridGlobals, DataGlobals, Globals
from smoderp2d.exceptions import ProviderError, ConfigError, GlobalsNotSet, \
    SmoderpError, RainDataError
from smoderp2d.providers import Logger
from smoderp2d.providers.base.exceptions import DataPreparationError


class Args:
    """TODO."""

    # type of computation (CompType)
    workflow_mode = None
    # path to pickle data file
    # used by 'dpre' for output and 'roff' for input
    data_file = None
    # config file
    config_file = None


class WorkflowMode:
    """TODO."""

    # type of computation
    dpre = 0  # data preparation only
    roff = 1  # runoff calculation only
    full = 2  # dpre + roff

    @classmethod
    def __getitem__(cls, key):
        if key == 'dpre':
            return cls.dpre
        elif key == 'roff':
            return cls.roff
        else:
            return cls.full


class BaseWriter(object):
    """TODO."""
    _raster_extension = '.asc'

    def __init__(self):
        self._data_target = None

    def set_data_layers(self, data):
        """Set data layers dictionary.

        :param data: data dictionary to be set
        """
        self._data_target = data

    def output_filepath(self, name, data_type=None, dirname_only=False):
        """
        Get correct path to store dataset 'name'.

        :param name: layer name to be saved
        :param data_type: None to determine target subdirectory
            from self._data_target
        :param dirname_only: True to return only path to parent directory

        :return: full path to the dataset
        """
        if data_type is None:
            data_type = self._data_target.get(name)
            defined_targets = ("temp", "control", "core")
            if data_type is None or data_type not in defined_targets:
                Logger.debug(
                   "Unable to define target in output_filepath for {}. Assuming temp.".format(name)
                )
                data_type = "temp"

        path = os.path.join(Globals.outdir, data_type) if data_type != 'core' else Globals.outdir
        if not os.path.exists(path):
            os.makedirs(path)
        if dirname_only:
            return path

        return os.path.join(path, name)

    @staticmethod
    def _print_array_stats(arr, file_output):
        """Print array stats.

        :param file_output: TODO
        """

        Logger.info("Raster ASCII output file <{}> saved".format(
            file_output
        ))
        if not isinstance(arr, np.ma.MaskedArray):
            na_arr = arr[arr != GridGlobals.NoDataValue]
        else:
            na_arr = arr
        Logger.info(
            "\tArray stats: min={0:.3f} max={1:.3f} mean={2:.3f}".format(
                na_arr.min(), na_arr.max(), na_arr.mean()
            )
        )

    def write_raster(self, array, output_name, data_type='core'):
        """Write raster (numpy array) to ASCII file.

        :param array: numpy array
        :param output_name: output filename
        :param data_type: directory where to write output file
        """
        file_output = BaseWriter.output_filepath(self, output_name, data_type)

        self._print_array_stats(
            array, file_output
        )

        self._write_raster(array, file_output)

    def create_storage(self, outdir):
        """TODO.

        :param outdir: TODO
        """
        pass

    @abstractmethod
    def _write_raster(self, array, file_output):
        """Write array into file.

        :param array: numpy array to be saved
        :param file_output: path to output file
        """
        pass

    @staticmethod
    def _check_globals():
        """Check globals to prevent call globals before values assigned.

        Raise GlobalsNotSet on failure.
        """
        if GridGlobals.xllcorner is None or \
            GridGlobals.yllcorner is None or \
            GridGlobals.dx is None or \
            GridGlobals.dy is None:
            raise GlobalsNotSet()


class BaseProvider(object):
    """TODO."""

    def __init__(self):
        self.args = Args()

        self._print_logo_fn = print

        # default logging level (can be modified by provider)
        Logger.setLevel(logging.INFO)

        # storage writer must be defined
        self.storage = None
        self._hidden_config = self.__load_hidden_config()

    @property
    def workflow_mode(self):
        return self.args.workflow_mode

    @abstractmethod
    def _postprocessing(self):
        """Perform provider-specific postprocessing.
        """
        pass

    @staticmethod
    def add_logging_handler(handler, formatter=None):
        """Register new logging handler.

        :param handler: logging handler to be registered
        :param formatter: logging handler formatting
        """
        if formatter is None:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
                "- [%(module)s:%(lineno)s]"
            )
        handler.setFormatter(formatter)
        Logger.addHandler(handler)

    def __load_hidden_config(self):
        """Load hidden configuration with advanced settings.

        return ConfigParser: object
        """
        if os.getenv("SMODERP2D_HIDDEN_CONFIG_FILE") is None:
            _path = os.path.join(
                os.path.dirname(__file__), '..', '..', '.config.ini'
            )
        else:
            _path = os.getenv("SMODERP2D_HIDDEN_CONFIG_FILE")
        if not os.path.exists(_path):
            raise ConfigError("{} does not exist".format(
                _path
            ))

        config = ConfigParser()
        config.read(_path)

        # set logging level
        Logger.setLevel(config.get('logging', 'level', fallback=logging.INFO))

        # set workflow mode
        self.args.workflow_mode = WorkflowMode()[config.get(
            'processes', 'workflow_mode', fallback="full"
        )]

        return config

    def _load_data_from_hidden_config(self, ignore=()):
        """Load data from hidden config.

        :param tuple ignore: list of options to me ignored

        :return: dict
        """
        data = {}
        data['prtTimes'] = self._hidden_config.get(
            'output', 'printtimes', fallback=None
        )
        data['extraout'] = self._hidden_config.getboolean(
            'output', 'extraout', fallback=False
        )
        data['computation_type'] = self._hidden_config.get(
            'computation_type', 'computation_type', fallback='explicit'
        )

        return data

    def _load_config(self):
        """TODO."""
        # load configuration
        if not os.path.exists(self.args.config_file):
            raise ConfigError("{} does not exist".format(
                self.args.config_file
            ))

        config = ConfigParser()
        config.read(self.args.config_file)

        try:
            # must be defined for _cleanup() method
            Globals.outdir = config.get('output', 'outdir')
        except (NoSectionError, NoOptionError) as e:
            raise ConfigError('Config file {}: {}'.format(
                self.args.config_file, e
            ))

        # sys.stderr logging
        self.add_logging_handler(
            logging.StreamHandler(stream=sys.stderr)
        )

        return config

    def _load_dpre(self):
        """Run data preparation procedure.

        See ArcGisProvider and GrassGisProvider for implementation issues.

        :return dict: loaded data
        """
        raise NotImplementedError()

    def _load_roff(self):
        """Load configuration data from roff computation procedure.

        :return dict: loaded data
        """
        from smoderp2d.processes import rainfall

        # the data are loaded from a pickle file
        try:
            data = self._load_data(self.args.data_file)
            if isinstance(data, list):
                raise ProviderError(
                    'Saved data out-dated. Please use '
                    'utils/convert-saved-data.py for update.'
                )
        except IOError as e:
            raise ProviderError('{}'.format(e))

        # some variables configs can be changes after loading from
        # pickle.dump such as end time of simulation
        if self._config.get('time', 'endtime'):
            data['end_time'] = self._config.getfloat('time', 'endtime')

        if self._config.get('processes', 'mfda'):
            data['mfda'] = self._config.getboolean(
                'processes', 'mfda', fallback=False
            )

        data['wave'] = self._config.get(
            'processes', 'wave', fallback='kinematic'
        )

        # type of computing
        data['type_of_computing'] = CompType()[
            self._config.get('processes', 'typecomp', fallback='stream_rill')
        ]

        #  rainfall data can be saved
        if self._config.get('data', 'rainfall'):
            try:
                data['sr'], data['itera'] = rainfall.load_precipitation(
                    self._config.get('data', 'rainfall')
                )
            except TypeError:
                raise ProviderError('Invalid rainfall file')
            except RainDataError as e:
                raise ProviderError(e)

        data['maxdt'] = self._config.getfloat('time', 'maxdt')

        # ensure that dx and dy are defined
        data['dx'] = data['dy'] = math.sqrt(data['pixel_area'])

        # load hidden config
        data.update(self._load_data_from_hidden_config())

        return data

    def load(self):
        """Load configuration data."""
        # cleanup output directory first
        self._cleanup()

        # log file need to be created after cleanup
        file_logger = os.path.join(Globals.outdir, "smoderp2d.log")
        self.add_logging_handler(
            logging.FileHandler(file_logger)
        )
        Logger.debug(f'File logger set to {file_logger}')

        data = None
        if self.args.workflow_mode in (WorkflowMode.dpre, WorkflowMode.full):
            try:
                data = self._load_dpre()
            except DataPreparationError as e:
                raise ProviderError('{}'.format(e))
            if self.args.workflow_mode == WorkflowMode.dpre:
                # data preparation requested only
                # add also related information from GridGlobals
                for k in ('NoDataValue', 'bc', 'br', 'c', 'dx', 'dy',
                          'pixel_area', 'r', 'rc', 'rr', 'xllcorner',
                          'yllcorner'):
                    data[k] = getattr(GridGlobals, k)
                self.args.data_file = os.path.join(
                    Globals.outdir, "dpre.save"
                )
                self.save_data(data, self.args.data_file)
                return

        if self.args.workflow_mode == WorkflowMode.roff:
            data = self._load_roff()

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

        Globals.mat_reten = -1.0 * data['mat_reten'] / 1000  # converts mm to m
        comp_type = self._comp_type(data['type_of_computing'])
        Globals.subflow = comp_type['subflow']
        Globals.isRill = comp_type['rill']
        Globals.isStream = comp_type['stream']
        # load hidden config
        hidden_config = self._load_data_from_hidden_config()
        if 'prtTimes' in data:
            Globals.prtTimes = data['prtTimes']
        else:
            Globals.prtTimes = hidden_config.get('prtTimes', None)
        if 'extraout' in data:
            Globals.extraOut = data['extraout']
        else:
            Globals.extraOut = hidden_config.get('extraout', False)
        if 'computation_type' in data:
            Globals.computationType = data['computation_type']
        else:
            Globals.computationType = hidden_config.get('computation_type', 'explicit')

        Globals.end_time *= 60  # convert min to sec

        # If profile1d provider is used the values
        # should be set in the loop at the beginning
        # of this method since it is part of the
        # data dict (only in profile1d provider).
        # Otherwise, it has to be set to 1.
        if Globals.slope_width is None:
            Globals.slope_width = 1

        # set masks of the area of interest
        GridGlobals.masks = [
            [True] * GridGlobals.c for _ in range(GridGlobals.r)
        ]
        rr, rc = GridGlobals.get_region_dim()
        for r in rr:
            for c in rc[r]:
                GridGlobals.masks[r][c] = False

    @staticmethod
    def _cleanup():
        """Clean-up output directory."""
        output_dir = Globals.outdir
        if not output_dir:
            # no output directory defined
            return
        if os.path.exists(output_dir):
            try:
                for filename in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            except PermissionError as e:
                raise ProviderError(
                    f"Unable to cleanup output directory: {e}"
                )
        else:
            try:
                os.makedirs(output_dir)
            except PermissionError as e:
                raise ProviderError(
                    f"Unable to create output directory: {e}"
                )

    @staticmethod
    def _comp_type(itc):
        """Returns boolean information about the components of the computation.

        Return true/values for rill, subflow, stream,
        presence/non-presence.

        :param CompType itc: type of computation

        :return dict:
        """
        ret = {}
        for item in ('sheet_only',
                     'rill',
                     'stream',
                     'subflow',
                     'subflow_rill',
                     'stream_subflow_rill'):
            ret[item] = False

        if itc == CompType.sheet_only:
            ret['sheet_only'] = True
        elif itc == CompType.rill:
            ret['rill'] = True
        elif itc == CompType.sheet_stream:
            ret['sheet_only'] = True
            ret['stream'] = True
        elif itc == CompType.stream_rill:
            ret['stream'] = True
            ret['rill'] = True
        elif itc == CompType.subflow:
            ret['subflow'] = True
        elif itc == CompType.subflow_rill:
            ret['subflow'] = True
            ret['rill'] = True
        elif itc == CompType.stream_subflow_rill:
            ret['stream'] = True
            ret['subflow'] = True
            ret['rill'] = True

        return ret

    def logo(self):
        """Print SMODERP2D ascii-style logo."""
        logo_file = os.path.join(os.path.dirname(__file__), 'txtlogo.txt')
        with open(logo_file, 'r') as fd:
            self._print_logo_fn(fd.read())
        self._print_logo_fn('')  # extra line

    @staticmethod
    def save_data(data, filename):
        """Save data into pickle.

        :param filename: TODO
        """
        if filename is None:
            raise ProviderError('Output file for saving data not defined')
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename, 'wb') as fd:
            pickle.dump(data, fd, protocol=2)
        Logger.info('Data preparation results stored in <{}> ({} bytes)'.format(
            filename, sys.getsizeof(data)
        ))

    @staticmethod
    def _load_data(filename):
        """Load data from pickle.

        :param str filename: file to be loaded
        :return: TODO
        """
        if filename is None:
            raise ProviderError('Input file for loading data not defined')
        with open(filename, 'rb') as fd:
            data = {
                key.decode() if isinstance(key, bytes) else key:
                val.decode() if isinstance(val, bytes) else val
                for key, val in pickle.load(fd, encoding='bytes').items()
            }
        Logger.debug('Size of loaded data is {} bytes'.format(
            sys.getsizeof(data))
        )

        return data

    def postprocessing(self, cumulative, surface_array, stream, inflows):
        """Perform postprocessing steps. Store results.

        :param cumulative: Cumulative object
        :param surface_array: numpy array
        :param stream: stream array (reach)
        :param inflows: inflows array
        """
        rrows = GridGlobals.rr
        rcols = GridGlobals.rc

        # compute maximum shear stress and velocity
        cumulative.calculate_vsheet_sheerstress()

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
                'q_sheet_tot',
                'vol_sheet',
                'h_rill',
                'q_rill_tot',
                'vol_rill',
                'b_rill',
                'inflow_sur',
                'sur_ret',
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
                cumulative.data[item].file_name,
                cumulative.data[item].data_type
            )

        # make extra rasters from cumulative clasess into temp dir
        for item in data_output_extras:
            self.storage.write_raster(
                self._make_mask(getattr(cumulative, item)),
                cumulative.data[item].file_name,
                cumulative.data[item].data_type
            )

        finState = np.zeros(np.shape(surface_array.state), np.float32)
        finState.fill(GridGlobals.NoDataValue)
        vRest = np.zeros(np.shape(surface_array.state), np.float32)
        vRest.fill(GridGlobals.NoDataValue)
        totalBil = cumulative.infiltration.copy()
        totalBil.fill(0.0)

        for i in rrows:
            for j in rcols[i]:
                finState[i][j] = int(surface_array.state.data[i, j])
                if finState[i][j] >= Globals.streams_flow_inc:
                    vRest[i][j] = GridGlobals.NoDataValue
                else:
                    vRest[i][j] = surface_array.h_total_new.data[i, j] * \
                                  GridGlobals.pixel_area

        totalBil = (cumulative.precipitation + cumulative.inflow_sur) - \
            (cumulative.infiltration + cumulative.vol_sur_tot) - \
            cumulative.sur_ret - vRest

        for i in rrows:
            for j in rcols[i]:
                if int(surface_array.state.data[i, j]) >= \
                        Globals.streams_flow_inc:
                    totalBil[i][j] = GridGlobals.NoDataValue

        self.storage.write_raster(
            self._make_mask(totalBil), 'massbalance', 'control'
        )
        self.storage.write_raster(
            self._make_mask(vRest), 'volrest_m3', 'control'
        )
        self.storage.write_raster(
            self._make_mask(finState), 'surfacestate', 'control'
        )

        # store stream reaches results to a table
        # if stream is calculated
        if stream:
            n = len(stream)
            m = 7
            outputtable = np.zeros([n, m])
            fid = list(stream.keys())
            for i in range(n):
                outputtable[i][0] = stream[fid[i]].segment_id
                outputtable[i][1] = stream[fid[i]].b
                outputtable[i][2] = stream[fid[i]].m
                outputtable[i][3] = stream[fid[i]].roughness
                outputtable[i][4] = stream[fid[i]].q365
                # TODO: The following should probably be made scalars already
                #       before in the code
                #       The following conditions are here meanwhile to be sure
                #       nothing went wrong
                if len(ma.unique(stream[fid[i]].V_out_cum)) > 2:
                    raise SmoderpError(
                        'Too many values in V_out_cum - More than one for one '
                        'stream'
                    )
                if len(ma.unique(stream[fid[i]].Q_max)) > 2:
                    raise SmoderpError(
                        'Too many values in Q_max - More than one for one '
                        'stream'
                    )
                outputtable[i][5] = ma.unique(stream[fid[i]].V_out_cum)[0]
                outputtable[i][6] = ma.unique(stream[fid[i]].Q_max)[0]

            np.savetxt(os.path.join(Globals.outdir, 'streams.csv'),
                       outputtable, delimiter=';', fmt='%.3e',
                       header='FID{sep}b_m{sep}m__{sep}rough_s_m1_3{sep}'
                              'q365_m3_s{sep}V_out_cum_m3{sep}'
                              'Q_max_m3_s'.format(sep=';'))

        if inflows is not None and Globals.mfda is False:
            # inflows are not stored for MFDA, see
            # https://github.com/storm-fsv-cvut/smoderp2d/issues/375
            inflows_array = np.zeros((GridGlobals.r, GridGlobals.c))
            # | -1 -1 | -1  0 | -1  1 |
            # |  0 -1 |  0  0 |  0  1 |
            # |  1 -1 |  1  0 |  1  1 |

            recode = {
                ( 0,  1): 1,
                ( 1,  1): 2,
                ( 1,  0): 4,
                ( 1, -1): 8,
                ( 0, -1): 16,
                (-1, -1): 32,
                (-1,  0): 64,
                (-1,  1): 128
            }
            for i in range(len(inflows)):
                for j in range(len(inflows[i])):
                    if_code = 0
                    for v in inflows[i][j]:
                        if_code += recode[tuple(v)]
                    inflows_array[i][j] = if_code

            self.storage.write_raster(
                self._make_mask(inflows_array), 'inflows', 'control'
            )

        # perform provider-specific postprocessing
        self._postprocessing()

    @staticmethod
    def _make_mask(arr):
        """ Assure that the no data value is outside the
        computation region.
        Works only for type float.

        :param arr: numpy array
        """
        rrows = GridGlobals.rr
        rcols = GridGlobals.rc

        copy_arr = arr.copy()
        arr.fill(GridGlobals.NoDataValue)

        for i in rrows:
            for j in rcols[i]:
                arr[i, j] = copy_arr[i, j]

        return arr
