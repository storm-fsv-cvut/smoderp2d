from smoderp2d.runners.base import Runner
                    
class GrassGisRunner(Runner):
    """TODO."""
    def _get_provider(self):
        from smoderp2d.providers.grass import GrassGisProvider
        return GrassGisProvider()

