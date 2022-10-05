import os
import sys
import configparser
import filecmp
from shutil import rmtree
from pathlib import Path
import pytest

def are_dir_trees_equal(dir1, dir2):
    """
    Taken from https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = Path(dir1) / common_dir
        new_dir2 = Path(dir2 / common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True

class TestCmd:
    config_file = Path(__file__).parent / "quicktest.ini"

    def test_001_read_config(self):
        assert Path(self.config_file).exists()

        config = configparser.ConfigParser()
        config.read(self.config_file)
        assert config['data']['rainfall'] == 'tests/data/rainfall.txt'

    def test_002_run(self):
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from smoderp2d import Runner

        config = configparser.ConfigParser()
        config.read(self.config_file)
        output_path = Path(config["output"]["outdir"])
        if output_path.exists():
            rmtree(output_path)

        os.environ["SMODERP2D_CONFIG_FILE"] = str(self.config_file)

        runner = Runner()
        runner.run()

        assert output_path.is_dir()

        assert are_dir_trees_equal(
            output_path,
            Path(__file__).parent / "data" / "reference" / "quicktest"
        )
