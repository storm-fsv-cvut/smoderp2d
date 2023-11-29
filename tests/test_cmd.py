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
    reference_dir = pytestconfig.getoption("reference_dir")
    if reference_dir is not None:
        reference_dir = os.path.join(
            os.path.dirname(__file__), pytestconfig.getoption("reference_dir")
        )
    _setup(request, config, reference_dir)
    yield


@pytest.mark.usefixtures('class_manager')
class TestCmd:
    def test_001_roff(self):
        PerformTest(Runner).run_roff(
            self.config_file, self.reference_dir
        )
