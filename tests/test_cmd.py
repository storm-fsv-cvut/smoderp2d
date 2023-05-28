import os
import pytest
import sys

from test_utils import PerformTest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import Runner

class TestCmd:
    def test_001_roff(self):
        PerformTest(Runner).run_roff(
            os.path.join(os.path.dirname(__file__), "quicktest.ini")
        )
