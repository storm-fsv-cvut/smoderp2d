import os
import sys
import configparser
import filecmp
import logging
from shutil import rmtree

from difflib import unified_diff

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
print(sys.path)
from smoderp2d.providers.base import CompType
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers import Logger

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
   def _print_diff_files(dcmp):
       for name in dcmp.same_files:
           print("same_file {} found in {} and {}".format(name, dcmp.left,
                 dcmp.right))
       for name in dcmp.diff_files:
           print("diff_file {} found in {} and {}".format(name, dcmp.left,
                 dcmp.right))
           with open(os.path.join(dcmp.left, name)) as left:
               with open(os.path.join(dcmp.right, name)) as right:
                   sys.stdout.writelines(unified_diff(left.readlines(), right.readlines()))

       for sub_dcmp in dcmp.subdirs.values():
           _print_diff_files(sub_dcmp)

   dirs_cmp = filecmp.dircmp(dir1, dir2)
   _print_diff_files(dirs_cmp)
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

class PerformTest:
    def __init__(self, runner, params_fn=None):
        self.runner = runner
        self._data_dir = os.path.join(os.path.dirname(__file__), "data")
        self._output_dir = os.path.join(
            self._data_dir, "output"
        )

        if params_fn:
            self._params = {
                'soil_type_fieldname': "SID",
                'vegetation_type_fieldname': "LandUse",
                'rainfall_file': os.path.join(self._data_dir, "rainfall.txt"),
                'maxdt': 30,
                'end_time': 40,
                'table_soil_vegetation_fieldname': "soilveg",
                'streams_channel_type_fieldname': "channel_id",
                'output': self._output_dir,
            }
            self._params.update(params_fn())
        else:
            self._params = None

    @staticmethod
    def _is_on_github_actions():
        # https://docs.github.com/en/actions/learn-github-actions/variables
        if "GITHUB_ACTION" in os.environ:
            return True
        return False

    @staticmethod
    def _extract_pickle_data(data_dict, target_dir):
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir)
        for k, v in data_dict.items():
            with open(os.path.join(target_dir, k), 'w') as fd:
                if isinstance(v, numpy.ndarray):
                    numpy.savetxt(fd, v)
                else:
                    fd.write(str(v))

    @staticmethod
    def _extract_target_dir(path):
        return os.path.join(os.path.dirname(path),
                            os.path.splitext(os.path.basename(path))[0] + '.extracted')

    @staticmethod
    def _data_to_str(data_dict):
        return [
            '{}:{}\n'.format(key,
                             numpy.array2string(value, threshold=numpy.inf) if isinstance(value, numpy.ndarray) else
                             value)
            for (key, value) in sorted(data_dict.items())
        ]

    @staticmethod
    def _compare_arrays(new_output_dict, reference_dict, target_dir):
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors

        for k, v in new_output_dict.items():
            if not isinstance(v, numpy.ndarray):
                continue
            diff = v - reference_dict[k]
            if diff.any():
                with open(os.path.join(target_dir, k+'.diff'), 'w') as fd:
                    numpy.savetxt(fd, diff)

                norm = mcolors.TwoSlopeNorm(vmin=diff.min(), vcenter=0, vmax=diff.max())
                plt.imshow(diff.astype(int), cmap='bwr', norm=norm)
                plt.colorbar()
                plt.savefig(os.path.join(target_dir, k+'_diff.png'))

    @staticmethod
    def report_pickle_difference(new_output, reference):
        """Report the inconsistency of two files.

        To be called when output comparison assert fails.

        :param new_output: path to the new output file
        :param reference: path to the reference file
        :return: string message reporting the content of the new output
        """
        diff_fn = new_output + '.diff'
        diff_fd = open(diff_fn, 'w')

        with open(new_output, 'rb') as left:
            with open(reference, 'rb') as right:
                if sys.version_info > (3, 0):
                    new_output_dict = pickle.load(left, encoding='bytes')
                    reference_dict = pickle.load(right, encoding='bytes')
                else:
                    new_output_dict = pickle.load(left)
                    reference_dict = pickle.load(right)

                if not is_on_github_actions():
                    self._extract_pickle_data(new_output_dict, _extract_target_dir(new_output))
                    self._extract_pickle_data(reference_dict, _extract_target_dir(reference))
                    self._compare_arrays(new_output_dict, reference_dict, _extract_target_dir(new_output))

                new_output_str = self._data_to_str(new_output_dict)
                reference_str = self._data_to_str(reference_dict)

                # sys.stdout.writelines(unified_diff(new_output_str, reference_str))
                diff_fd.writelines(unified_diff(new_output_str, reference_str))

        diff_fd.close()

        return f'Inconsistency in {new_output} compared to the reference data. ' \
               f'The diff can be seen above and is stored in {diff_fn}.'

    def _run(self, comptype=None):
        runner = self.runner()
        Logger.setLevel(logging.ERROR)
        if self._params:
            runner.set_options(self._params)

        if comptype is not None:
            runner.set_comptype(comptype)

        try:
            runner.run()
        except ProviderError as e:
            sys.exit(e)
        
    def run_dpre(self):
        self._run(CompType.dpre)

        dataprep_filepath = os.path.join(self._output_dir, 'dpre.save')
        reference_filepath = os.path.join(
            self._output_dir, '..', 'reference', 'gistest', 'dpre',
            'arcgis' if 'GRASS_OVERWRITE' not in os.environ else 'grass',
            'dpre.save')
        assert filecmp.cmp(dataprep_filepath, reference_filepath),\
            self.report_pickle_difference(dataprep_filepath, reference_filepath)

    def run_roff(self, config_file):
        assert os.path.exists(config_file)

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.get('data', 'rainfall') == 'tests/data/rainfall.txt'
        
        os.environ["SMODERP2D_CONFIG_FILE"] = str(config_file)
        self._run()
        
        assert os.path.isdir(self._output_dir)

        assert are_dir_trees_equal(
            self._output_dir,
            os.path.join(os.path.dirname(__file__), "data", "reference",
                         os.path.splitext(os.path.basename(config_file))[0])
        )

    def run_full(self):
        self._run(CompType.full)

        assert os.path.isdir(self._output_dir)

        assert are_dir_trees_equal(
            self._output_dir,
            os.path.join(self._data_dir, "reference", "gistest", "full")
        )        

class TestCmdBase:
    config_file = None

    def do_001_read_config(self):
        assert os.path.exists(self.config_file)

        config = configparser.ConfigParser()
        config.read(self.config_file)
        assert config.get('data', 'rainfall') == 'tests/data/rainfall.txt'

    def do_002_run(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from smoderp2d import Runner

        config = configparser.ConfigParser()
        config.read(self.config_file)
        self._output_dir = config.get("output", "outdir")
        if os.path.exists(self._output_dir):
            rmtree(self._output_dir)

        os.environ["SMODERP2D_CONFIG_FILE"] = str(self.config_file)

        runner = Runner()
        runner.run()

        assert os.path.isdir(self._output_dir)

        assert _are_dir_trees_equal(
            self._output_dir,
            os.path.join(os.path.dirname(__file__), "data", "reference",
                         os.path.splitext(os.path.basename(self.config_file))[0])
        )
