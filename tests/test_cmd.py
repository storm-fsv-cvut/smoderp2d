import os
import sys
from pathlib import Path
import pytest

class TestCmd:
    config_file = Path(__file__).parent / "quicktest.ini"

    def test_001_read_config(self):
        import configparser

        assert Path(self.config_file).exists()

        config = configparser.ConfigParser()
        config.read(self.config_file)
        assert config['data']['rainfall'] == 'tests/data/rainfall.txt'

    def test_002_run(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

        from start import start_smoderp2d
        os.environ["SMODERP2D_CONFIG_FILE"] = str(self.config_file)
        start_smoderp2d()

        output_path = Path(__file__).parent / "data" / "output"
        print(output_path)
