import os
import pytest

from smoderp2d import Runner

from test_utils import PerformTest

class TestCmd:
    def test_001_roff(self):
        PerformTest(Runner).run_roff(
            os.path.join(os.path.dirname(__file__), "quicktest.ini")
        )
