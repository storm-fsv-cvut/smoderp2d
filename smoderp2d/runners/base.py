
import os
from abc import abstractmethod

from smoderp2d.core.general import Globals, GridGlobals
from smoderp2d.providers import Logger
from smoderp2d.providers.base import WorkflowMode
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput
from smoderp2d.exceptions import SmoderpError, ProviderError


class Runner(object):
    """Run SMODERP2D."""

    def __init__(self):
        self._provider = self._get_provider()

    def _get_provider(self):
        """Get provider object instance.

        :return provider class instance
        """
        if os.getenv('SMODERP2D_PROFILE1D'):
            from smoderp2d.providers.profile1d import Profile1DProvider
            provider_class = Profile1DProvider()
        else:
            from smoderp2d.providers.cmd import CmdProvider
            provider_class = CmdProvider()

        return provider_class

    @property
    def workflow_mode(self):
        """Get workflow mode."""
        return self._provider.args.workflow_mode

    @workflow_mode.setter
    def workflow_mode(self, workflow_mode):
        """Set computation type.

        :param WorkflowMode workflow_mode: workflow mode
        """
        self._provider.args.workflow_mode = workflow_mode
        if workflow_mode in (WorkflowMode.dpre, WorkflowMode.roff):
            self._provider.args.data_file = os.path.join(
                Globals.outdir, "dpre.save"
            )

    def run(self):
        """Perform computation."""
        # print logo
        self._provider.logo()

        # check workflow_mode consistency
        modes = (WorkflowMode.dpre, WorkflowMode.roff, WorkflowMode.full)
        if self._provider.workflow_mode not in modes:
            raise ProviderError('Unsupported partial computing: {}'.format(
                self._provider.workflow_mode
            ))

        # set percentage counter
        if self._provider.workflow_mode == WorkflowMode.dpre:
            Logger.set_progress(100)
        elif self._provider.workflow_mode == WorkflowMode.full:
            Logger.set_progress(40)
        else:
            Logger.set_progress(10)

        # load configuration (set global variables)
        try:
            self._provider.load()
        except DataPreparationInvalidInput:
            return 1

        if self._provider.args.workflow_mode == WorkflowMode.dpre:
            # data preparation only requested
            return

        # must be called after initialization (!)
        from smoderp2d.runoff import Runoff

        # set percentage counter for counter
        Logger.set_progress(95)

        # run computation
        runoff = Runoff(self._provider)
        runoff.run()

        # save result data
        Logger.set_progress(100)
        runoff.save_output()

        # resets
        Logger.reset()

        return 0

    @property
    def options(self):
        """Get provider options."""
        return self._provider._options

    def set_options(self, options):
        """Set options.

        :param options: options to be set by provider
        """
        self._provider.set_options(options)

    def finish(self):
        """Finish runner's operations."""
        # reset handlers
        Logger.handlers = []

        # reset globals
        Globals.reset()
        GridGlobals.reset()
