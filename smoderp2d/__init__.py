"""
Documentation of Smoderp, distributed event-based model for surface and subsurface runoff and erosion.

.. moduleauthor:: Petr Kavka, Karel Vrana and Jakub Jerabek
                  model was build in cooperation with eng. students (Jan Zajicek, Nikola Nemcova, Tomas Edlman, Martin Neumann)

The computational options are as follows:
 - Type of flow
  - surface
   - subsurface
   - surface + subsurface
 - Flow direction algorithm
   - D8 (default)
   - multi-flow direction
 - Erosion
   - none
   - sheet erosion
   - sheet erosion + rill erosion
 - Stream
   - yes
   - no
"""

import os

from smoderp2d.core.general import Globals
from smoderp2d.providers import Logger
from smoderp2d.providers.base import WorkflowMode
from smoderp2d.providers.base.exceptions import DataPreparationInvalidInput
from smoderp2d.exceptions import SmoderpError

__version__ = "2.0.dev"

class Runner(object):
    def __init__(self):
        provider_class = self._provider_factory()
        self._provider = provider_class()

    def _provider_factory(self):
        # initialize provider
        if isinstance(self, ArcGisRunner):
            from smoderp2d.providers.arcgis import ArcGisProvider
            provider_class = ArcGisProvider
        elif isinstance(self, GrassGisRunner):
            from smoderp2d.providers.grass import GrassGisProvider
            provider_class = GrassGisProvider
        elif os.getenv('SMODERP2D_PROFILE1D'):
            from smoderp2d.providers.profile1d import Profile1DProvider
            provider_class = Profile1DProvider
        else:
            from smoderp2d.providers.cmd import CmdProvider
            provider_class = CmdProvider

        return provider_class

    @property
    def workflow_mode(self):
        return self._provider.args.workflow_mode

    @workflow_mode.setter
    def workflow_mode(self, workflow_mode):
        """Set computation type.

        :param WorkflowMode workflow_mode: workflow mode
        """
        self._provider.args.workflow_mode = workflow_mode
        if workflow_mode in (WorkflowMode.dpre, WorkflowMode.roff):
            self._provider.args.data_file = os.path.join(Globals.outdir, "dpre.save")

    def run(self):
        # print logo
        self._provider.logo()

        # check workflow_mode consistency
        if self._provider.workflow_mode not in (WorkflowMode.dpre, WorkflowMode.roff, WorkflowMode.full):
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
            # data prepararation only requested
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

        return 0

    def set_options(self, options):
        self._provider.set_options(options)

class ArcGisRunner(Runner):
    def __init__(self):
        os.environ['ESRIACTIVEINSTALLATION'] = '1'
        super(ArcGisRunner, self).__init__()

class GrassGisRunner(Runner):
    pass

class QGISRunner(GrassGisRunner):
    def __init__(self):
        # create temp GRASS location
        import subprocess
        import tempfile
        import binascii
        import grass.script as gs
        from grass.script import setup as gsetup

        # path to temp location
        gisdb = os.path.join(tempfile.gettempdir(), 'grassdata')
        if not os.path.isdir(gisdb):
            os.mkdir(gisdb)

        # location: use random names for batch jobs
        string_length = 16
        location = binascii.hexlify(os.urandom(string_length)).decode("utf-8")

        subprocess.call(
            ['grass', '-e', '-c EPSG:5514', os.path.join(gisdb, location)]
        )

        # initialize GRASS session
        gsetup.init(gisdb, location, 'PERMANENT', os.environ['GISBASE'])

        # create location
        try:
            gs.create_location(gisdb, location, epsg='5514', overwrite=True)
        except SmoderpError as e:
            raise SmoderpError('{}'.format(e))

        # test GRASS env varible
        if not os.getenv('GISRC'):
            raise SmoderpError('GRASS not found.')

        super().__init__()

    def import_data(self, options):
        """
        Import files to grass

        :param options: dictionary of input data
        """
        from grass.pygrass.modules import Module

        for key in options:
            try:
                # import rasters
                if key == "elevation":
                    Module("r.import", input=options[key], output=key)
                # import vectors
                elif key in ["soil", "vegetation", "points", "stream"]:
                    Module("v.import", input=options[key], output=key, flags = 'o')
                # import tables
                elif key in ["table_soil_vegetation", "table_stream_shape"]:
                    Module("db.in.ogr", input=options[key], output=key)
            except SmoderpError as e:
                raise SmoderpError('{}'.format(e))

    def export_data(self):
        pass

    def __del__(self):
        pass

class WpsRunner(Runner):
    def __init__(self, **args):
        provider_class = self._provider_factory()
        self._provider = provider_class(**args)
