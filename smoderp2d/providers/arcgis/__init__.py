import sys

import arcpy

from smoderp2d.providers.base import BaseProvider
from smoderp2d.providers.arcgis import constants

class ArcGisProvider(BaseProvider):
    class Args:
        typecomp = None
    
    def __init__(self):
        super(ArcGisProvider, self).__init__()

        self._agrs = Args()
        self._args.typecomp = self._get_argv(
            constants.PARAMETER_PARTIAL_COMPUTING
        )

        @staticmethod
        def get_argv(idx):
            return sys.argv[idx+1]

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        from smoderp2d.data_preparation.data_preparation import PrepareData
       
        return PrepareData().run()
        
    def load(self):
        """Load configuration data."""
        if self._args.typecomp not in ('dpre', 'roff', 'full'):
            raise ProviderError('Unsupported partial computing: {}'.format(
                self._args.typecomp
            ))

        data = None
        if self._args.typecomp in ('dpre', 'full'):
            data = self._load_dpre()
            if self._args.typecomp == 'dpre':
                # data preparation requested only
                from smoderp2d.tools.save_load_data import save_data
                out_file = os.path.join(
                    self._get_argv(constants.PARAMETER_PATH_TO_OUTPUT_DIRECTORY),
                    self._get_argv(constants.PARAMETER_INDATA)
                )
                save_data(data, out_file)
                return

        if self._args.typecomp == 'roff':
            data = self._load_roff(
                self._get_argv(constants.PARAMETER_INDATA)
            )

        # roff || full
        self._set_globals(data)
        self._cleanup()
