import os
import pytest
import sys

from test_utils import PerformTest


@pytest.fixture(scope='class')
def class_manager(request, pytestconfig):
    config = os.path.join(os.path.dirname(__file__), pytestconfig.getoption("config"))
    _setup(request, config)
    yield


@pytest.mark.usefixtures('class_manager')
class TestCmd(TestCmdBase):
    def test_001_read_config(self):
        self.do_001_read_config()

    def test_002_run(self):
        self.do_002_run()
