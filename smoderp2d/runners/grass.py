from smoderp2d.runners.base import Runner
                    
class GrassGisRunner(Runner):
    """Run SMODERP2D in GRASS GIS environment."""
    def _get_provider(self):
        """See base method for description.
        """
        from smoderp2d.providers.grass import GrassGisProvider
        return GrassGisProvider()

