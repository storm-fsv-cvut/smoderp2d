import os
import sys
import pytest

from test_utils import PerformTest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import Runner


class TestCmd:
    def test_001_roff(self):
        os.environ["SMODERP2D_PROFILE1D"] = "1"

        PerformTest(Runner).run_roff(
            os.path.join(os.path.dirname(__file__), "profile1d.ini")
        )
