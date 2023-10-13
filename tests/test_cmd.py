import os
import pytest
import sys

from test_utils import PerformTest, _setup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d import Runner


@pytest.fixture(scope='class')
def class_manager(request, pytestconfig):
    config = os.path.join(
        os.path.dirname(__file__), pytestconfig.getoption("config")
    )
    _setup(request, config)
    yield


@pytest.mark.usefixtures('class_manager')
class TestCmd:
    def test_001_roff(self):
        PerformTest(Runner).run_roff(
            self.config_file
        )
