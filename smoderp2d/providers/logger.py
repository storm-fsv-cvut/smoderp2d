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
        self.aborted = False

    def set_progress(self, end):
        """Set percentage progress counter.

        :param int end: end value in %
        """
        self._progress_info = {
            'start': self._progress_info['end'],
            'end': int(end)
        }
        self._progress_info['range'] = \
            self._progress_info['end'] - self._progress_info['start']

    def progress(self, perc, *args):
        if self.aborted is True:
            self.aborted = False
            self.reset()
            from smoderp2d.exceptions import ComputationAborted
            raise ComputationAborted()
        if args:
            self._progress(perc, *args)
        perc_int = int(
            self._progress_info['start'] + (perc / 100.0) * self._progress_info['range']
        )
        if self.isEnabledFor(PROGRESS):
            self._log(PROGRESS, perc_int, None)
        else:
            self.info("Progress value: {}%".format(perc_int))

    def _progress(self, perc, delta_t, t_iter, total_time):
        self.info('-' * 80)
        self.info("Total time      [secs]: {0:.2f}".format(total_time))
        self.info("Time step       [secs]: {0:.2e}".format(delta_t))
        self.info("Time iterations       : {0:d}".format(t_iter))
        self.info("Percentage done    [%]: {0:.2f}".format(perc))
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

        self.info("Time to end    {0}: {1:.2f}".format(units, remaining))
        self.info('-' * 80)

    def reset(self):
        self._progress_info = {
            'start': 0,
            'end': 0,
            'range': 0
        }
