from smoderp2d.runners.base import Runner

class WpsRunner(Runner):
    """Run SMODERP2D as WPS process."""
    def __init__(self, **args):
        """Initialize runner."""
        provider_class = self._provider_factory()
        self._provider = provider_class(**args)
