import sys
if sys.version_info.major >= 3:
    from configparser import ConfigParser, NoSectionError
else:
    from ConfigParser import ConfigParser, NoSectionError

from smoderp2d.providers.base import BaseProvider

class WpsProvider(BaseProvider):
    def __init__(self):
        """WPS provider."""
        super(WpsProvider, self).__init__()

        self._config = ConfigParser()

    def set_options(self, options):
        """Set input paramaters.

        :param options: options dict to set
        """
        self._config.read(options['indata'])

    def load(self):
        """Load configuration data.

        Only roff procedure supported.
        """
        # cleanup output directory first
        self._cleanup()

        data = self._load_roff(
            self._config.get('Other', 'indata')
        )

        self._set_globals(data)
