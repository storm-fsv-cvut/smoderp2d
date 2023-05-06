import os
import pytest

from test_utils import TestCmdBase, _setup

os.environ["SMODERP2D_PROFILE1D"] = "1"
config_file = os.path.join(os.path.dirname(__file__), "profile1d.ini")

@pytest.fixture(scope='class')
def class_manager(request):
    _setup(request, config_file)
    yield
    
@pytest.mark.usefixtures('class_manager')
class TestProfile1d(TestCmdBase):
    def test_001_read_config(self):
        self.do_001_read_config()

    def test_002_run(self):
        self.do_002_run()
