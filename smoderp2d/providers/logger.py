import time
import logging

import numpy as np

# custom logging level
PROGRESS = 101
logging.addLevelName(PROGRESS, "PROGRESS")

class BaseLogger(logging.Logger):
    def __init__(self, name):
        super(BaseLogger, self).__init__(name)
        self.start_time = time.time()
        self._progress_info = {
            'start': 0,
            'end': 0,
            'range': 0
        }

    def set_progress(self, end):
        """Set percentage progress counter.

        :param int end: end value in %
        :param int start: start value in %
        """
        self._progress_info = {
            'start': self._progress_info['end'],
            'end': int(end)
        }
        self._progress_info['range'] = \
            self._progress_info['end'] - self._progress_info['start']

    def progress(self, perc, *args, **kwargs):
        self._progress(perc, *args)
        # The commented code bellow caused problems with arcgis.
        #if args:
        #    self._progress(perc, *args)
        #    args = ()
        #if self.isEnabledFor(PROGRESS):
        #    perc_int = int(
        #        self._progress_info['start'] + (perc/100.0) * self._progress_info['range']
        #    )
        #    self._log(PROGRESS, perc_int, args, **kwargs)
        #else:
        #    self.info("Progress value: {}%".format(perc_int))

    def _progress(self, perc, delta_t, t_iter, total_time):
        self.info('-' * 80)
        self.info("Total time      [secs]: {0:.2f}".format(total_time[0, 0])) # TODO: ms ???
        self.info("Time step       [secs]: {0:.2e}".format(delta_t[0, 0]))
        self.info("Time iterations       : {0:d}".format(t_iter))
        self.info("Percentage done    [%]: {0:.2f}".format(perc[0, 0]))
        units = ' [secs]'
        if np.any(perc > 0):
            diff_time = time.time() - self.start_time
            remaining = (100.0 * diff_time) / perc - diff_time
        else:
            remaining = '[??]'
        if np.any(remaining > 60):
            remaining /= float(60)
            units = ' [mins]'
        elif np.any(remaining > 60 * 60):
            remaining /= float(60 * 60)
            units = '[hours]'
        elif np.any(remaining > 60 * 60 * 24):
            remaining /= float(60 * 60 * 24)
            units = ' [days]'

        self.info("Time to end    {0}: {1:.2f}".format(units, remaining[0, 0]))
        self.info('-' * 80)
