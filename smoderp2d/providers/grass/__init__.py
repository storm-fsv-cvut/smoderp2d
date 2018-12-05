# TODO: not tested yet

from smoderp2d.providers.base import BaseProvider

class GrassProvider(BaseProvider):
    def __init__(self):
        super(GrassProvider, self).__init__()

    def _load_dpre(self):
        """Load configuration data from data preparation procedure.

        :return dict: loaded data
        """
        raise NotImplemenetedError("To be implemented")
