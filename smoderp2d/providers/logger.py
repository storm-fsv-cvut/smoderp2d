import time
import logging

# custom logging level
PROGRESS_INFO = 101
logging.addLevelName(PROGRESS_INFO, "PROGRESS_INFO")

class BaseLogger(logging.Logger):
    def __init__(self, name):
        super(BaseLogger, self).__init__(name)
        self.start_time = time.time()

    def set_progress(self, start, end):
        """Set percentage progress counter.

        :param int start: start value in %
        :param int end: end value in %
        """
        self._progress_info = {
            'start': int(start),
            'end': int(end),
            'range': int(end) - int(start)
        }

    def progress(self, perc, *args, **kwargs):
        if args:
            self._progress(perc, *args)
        if self.isEnabledFor(PROGRESS_INFO):
            perc_int = int(
                self._progress_info['start'] + (perc/100.0) * self._progress_info['range']
            )
            self._log(PROGRESS_INFO, perc_int, args, **kwargs)
        else:
            self.info("Progress value: {}%".format(perc_int))

    def _progress(self, perc, delta_t, t_iter, total_time):
        self.info('-' * 80)
        self.info("Total time      [secs]: {0:.2f}".format(total_time)) # TODO: ms ???
        self.info("Time step       [secs]: {0:.2e}".format(delta_t))
        self.info("Time iterations       : {0:d}".format(t_iter))
        self.info("Percentage done    [%]: {0:.2f}".format(perc))
        units = ' [secs]'
        if perc > 0:
            diff_time = time.time() - self.start_time
            remaining = (100.0 * diff_time) / perc - diff_time
        else:
            remaining = '[??]'
        if remaining > 60:
            remaining /= float(60)
            units = ' [mins]'
        elif remaining > 60*60:
            remaining /= float(60*60)
            units = '[hours]'
        elif remaining > 60*60*24.:
            remaining /= float(60*60*24)
            units = ' [days]'

        self.info("Time to end    {0}: {1:.2f}".format(units, remaining))
        self.info('-' * 80)
