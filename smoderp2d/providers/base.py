import os
import sys
import argparse
import shutil
import math
import time
import ConfigParser

from smoderp2d.core.general import Globals
from smoderp2d.providers.logger import Logger
from smoderp2d.exceptions import ProviderError

class BaseProvider(object):
    def __init__(self):
        """Create argument parser."""
        # define CLI parser
        self._parser = argparse.ArgumentParser()
        self._parser.add_argument(
            'typecomp',
            help='type of computation',
            type=str,
            choices=['full',
                     'dpre',
                     'roff']
        )
        self._parser.add_argument(
            'indata',
            help='file with input data',
            type=str
        )
        self._args = self._parser.parse_args()

        # load configuration
        self._config = ConfigParser.ConfigParser()
        self._config.read(self._args.indata)

        # set logging level
        Logger.setLevel(self._config.get('Other', 'logging'))

        # progress
        self.startTime = time.time()

    def parse_data(self, indata):
        # TODO: rewrite save pickle to use dict instead of list
        
        data = {}
        data['br'],                       \
        data['bc'],                       \
        data['mat_boundary'],             \
        data['rr'],                       \
        data['rc'],                       \
        data['outletCells'],              \
        data['xllcorner'],                \
        data['yllcorner'],                \
        data['NoDataValue'],              \
        data['array_points'],             \
        data['c'],                        \
        data['r'],                        \
        data['combinatIndex'],            \
        data['delta_t'],                  \
        data['mat_pi'],                   \
        data['mat_ppl'],                  \
        data['surface_retention'],        \
        data['mat_inf_index'],            \
        data['mat_hcrit'],                \
        data['mat_aa'],                   \
        data['mat_b'],                    \
        data['mat_reten'],                \
        data['mat_fd'],                   \
        data['mat_dmt'],                  \
        data['mat_efect_vrst'],           \
        data['mat_slope'],                \
        data['mat_nan'],                  \
        data['mat_a'],                    \
        data['mat_n'],                    \
        data['outdir'],                   \
        data['pixel_area'],               \
        data['points'],                   \
        data['poradi'],                   \
        data['end_time'],                 \
        data['spix'],                     \
        data['state_cell'],               \
        data['temp'],                     \
        data['type_of_computing'],        \
        data['vpix'],                     \
        data['mfda'],                     \
        data['sr'],                       \
        data['itera'],                    \
        data['toky'],                     \
        data['cell_stream'],              \
        data['mat_tok_reach'],            \
        data['STREAM_RATIO'],             \
        data['toky_loc'] = indata

        return data
        
    def _load_roff(self, indata):
        """Load configuration data for roff compurtation only.

        :param str indata: configuration filename

        :return dict: loaded data
        """
        from smoderp2d.tools.save_load_data import load_data
        from smoderp2d.processes import rainfall

        # the data are loared from a pickle file
        try:
            data = self.parse_data(load_data(indata))
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
    
    def _set_globals(self, data):
        """Set global variables.

        :param dict data: data to be set
        """
        for item in data.keys():
            if not hasattr(Globals, item):
                continue
            setattr(Globals, item, data[item])

        Globals.NoDataInt = int(-9999)
        Globals.dx = math.sqrt(data['pixel_area'])
        Globals.dy = Globals.dx
        Globals.mat_reten = -1.0 * data['mat_reten'] / 1000
        Globals.diffuse = self._comp_type(data['type_of_computing'])['diffuse']
        Globals.subflow = self._comp_type(data['type_of_computing'])['subflow']
        # TODO: lines below are part only of linux method
        Globals.isRill = self._comp_type(data['type_of_computing'])['rill']
        Globals.isStream = self._comp_type(data['type_of_computing'])['stream']
        Globals.arcgis = False
        Globals.prtTimes = data['prtTimes']
        
    def _cleanup(self):
        """Clean-up output directory."""
        output = Globals.outdir
        if os.path.exists(output):
            shutil.rmtree(output)
        os.makedirs(output)
        
    def load(self):
        """Load configuration data."""
        if self._args.typecomp == 'roff':
            data = self._load_roff(
                self._config.get('Other', 'indata')
            )

            self._set_globals(data)
            self._cleanup()
        else:
            raise ProviderError('Unsupported partial computing: {}'.format(
                self._args.typecomp
            ))

    def _comp_type(self, tc):
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
        
    def message(self, line):
        """Print message.

        :param str line: string to be printed
        """
        sys.stdout.write('{}{}'.format(line, os.linesep))

    def progress(self, i, dt, iter_, total_time):
        self.message("Total time      [s]: {0:.2f}".format(total_time)) # TODO: ms ???
        self.message("Time step       [s]: {0:.2f}".format(dt))
        self.message("Time iterations    : {0:d}".format(iter_))
        self.message("Percentage done [%]: {0:.2f}".format(i))
        if i > 0:
            diffTime = time.time() - self.startTime
            remaining = (100.0 * diffTime) / i - diffTime
        else:
            remaining = '??'
        self.message("Time to end     [s]: {0:.2f}".format(remaining))
        self.message("-" * 40)
        
    def logo(self):
        """Print Smoderp2d ascii-style logo."""
        with open(os.path.join(os.path.dirname(__file__), 'txtlogo.txt'), 'r') as fd:
            for line in fd.readlines():
                line = line.rstrip('\n')
                self.message(line)
