import os
import sys
import configparser
import filecmp
from shutil import rmtree
import pytest


def print_diff_files(dcmp):
    for name in dcmp.diff_files:
        print("diff_file {} found in {} and {}".format(name, dcmp.left,
              dcmp.right))

    for sub_dcmp in dcmp.subdirs.values():
        print_diff_files(sub_dcmp)


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
    print_diff_files(dirs_cmp)
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


class TestCmd:
    config_file = os.path.join(os.path.dirname(__file__), "quicktest.ini")

    def test_001_read_config(self):
        assert os.path.exists(self.config_file)

        config = configparser.ConfigParser()
        config.read(self.config_file)
        assert config.get('data', 'rainfall') == 'tests/data/rainfall.txt'

    def test_002_run(self, capsys):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from smoderp2d import Runner

        config = configparser.ConfigParser()
        config.read(self.config_file)
        output_path = config.get("output", "outdir")
        if os.path.exists(output_path):
            rmtree(output_path)

        os.environ["SMODERP2D_CONFIG_FILE"] = str(self.config_file)

        runner = Runner()
        runner.run()

        assert os.path.isdir(output_path)

        are_dir_trees_equal(
            output_path,
            os.path.join(os.path.dirname(__file__), "data", "reference", "quicktest")
        )

        cap = capsys.readouterr()

        with open(f'/tmp/out.txt', 'w') as out:
            out.write(cap.out)

        # assert are_dir_trees_equal(
        #     output_path,
        #     os.path.join(os.path.dirname(__file__), "data", "reference", "quicktest")
        # )
