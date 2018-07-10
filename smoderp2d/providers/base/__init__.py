import os
import sys
import shutil
import math

from smoderp2d.core.general import GridGlobals, DataGlobals, Globals
from smoderp2d.providers.base.logger import logger
from smoderp2d.exceptions import ProviderError

Logger = logger()

class BaseProvider(object):
    def __init__(self):
        pass

    def _load_dpre(self):
        """ Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        raise NotImplemenetedError()

    def _load_roff(self, indata):
        """Load configuration data from roff computation procedure.

        :param str indata: configuration filename

        :return dict: loaded data
        """
        from smoderp2d.tools.save_load_data import load_data
        from smoderp2d.processes import rainfall

        # the data are loared from a pickle file
        try:
            data = load_data(indata)
            if isinstance(data, list):
                raise ProviderError('Saved data out-dated. Please use utils/convert-saved-data.py for update.')
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
        """Load configuration data.
        """
        raise NotImplementedError("Must be implemeneted by superclass")

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
        Globals.arcgis = False
        Globals.prtTimes = data['prtTimes']

    @staticmethod
    def _cleanup():
        """Clean-up output directory."""
        output = Globals.outdir
        if os.path.exists(output):
            shutil.rmtree(output)
        os.makedirs(output)
        
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

    @staticmethod
    def logo():
        """Print Smoderp2d ascii-style logo."""
        with open(os.path.join(os.path.dirname(__file__), 'txtlogo.txt'), 'r') as fd:
            for line in fd.readlines():
                sys.stdout.write(line)
        sys.stdout.write(os.linesep)
        sys.stdout.flush()
