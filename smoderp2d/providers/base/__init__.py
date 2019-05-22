from __future__ import print_function

import os
import sys
import shutil
import math
import pickle
import logging
import tensorflow as tf

from smoderp2d.providers import Logger
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
        raise NotImplemenetedError()

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
            data = self._load_dpre()
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

        # for TF implementation
        # TODO: Change all data to TF Variables
        nodata = tf.equal(data['mat_efect_cont'], -3.40282347e+38)
        nodata_pos = tf.constant(
            [[3.40282347e+38, ] * nodata.shape[1], ] * nodata.shape[0],
            dtype=tf.float64)
        data['mat_efect_cont_tf'] = tf.where(nodata, nodata_pos,
                                             data['mat_efect_cont'])
        data['rr_tf'] = tf.constant(data['rr'], dtype=tf.int32)
        data['rc_tf'] = tf.constant(data['rc'], dtype=tf.int32)
        data['mat_n_tf'] = tf.constant(data['mat_n'], dtype=tf.float64)
        data['mat_slope_tf'] = tf.constant(data['mat_slope'], dtype=tf.float64)

        return data
