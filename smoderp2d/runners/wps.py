from smoderp2d.runners.base import Runner

class WpsRunner(Runner):
    """TODO."""

    def __init__(self, **args):
        """TODO."""
        provider_class = self._provider_factory()
        self._provider = provider_class(**args)
