import os
import pytest
import sys

from test_utils import PerformTest, _setup

from smoderp2d.runners.base import Runner


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
    hidden_config = pytestconfig.getoption("hidden_config")
    if hidden_config is not None:
        hidden_config = os.path.join(
            os.path.dirname(__file__), pytestconfig.getoption("hidden_config")
        )

    _setup(request, config, reference_dir, hidden_config)
    yield


@pytest.mark.usefixtures('class_manager')
class TestCmd:
    def test_001_roff(self):
        PerformTest(Runner, self.reference_dir).run_roff(
            self.config_file, self.hidden_config
        )
