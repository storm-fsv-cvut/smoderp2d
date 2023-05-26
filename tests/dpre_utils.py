import os
import sys
import pickle
import filecmp
import shutil
import numpy
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    has_matplotlib = True
except ModuleNotFoundError:
    has_matplotlib = False

from difflib import unified_diff

from smoderp2d import ArcGisRunner
from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import CompType

data_dir = os.path.join(os.path.dirname(__file__), "data")
output_dir = os.path.join(data_dir, "output")

def extract_pickle_data(data_dict, target_dir):
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)
    for k, v in data_dict.items():
        with open(os.path.join(target_dir, k), 'w') as fd:
            if isinstance(v, numpy.ndarray):
                numpy.savetxt(fd, v)
            else:
                fd.write(str(v))

def _extract_target_dir(path):
    return os.path.join(os.path.dirname(path),
                        os.path.splitext(os.path.basename(path))[0] + '.extracted')

def _data_to_str(data_dict):
    return [
        '{}:{}\n'.format(key,
                         numpy.array2string(value, threshold=numpy.inf) if isinstance(value, numpy.ndarray) else
                         value)
        for (key, value) in sorted(data_dict.items())
    ]

def compare_arrays(new_output_dict, reference_dict, target_dir):
    for k, v in new_output_dict.items():
        if not isinstance(v, numpy.ndarray):
            continue
        diff = v - reference_dict[k]
        with open(os.path.join(target_dir, k+'.diff'), 'w') as fd:
            numpy.savetxt(fd, diff)
        if not has_matplotlib:
            continue

        if diff.any():
            norm = mcolors.TwoSlopeNorm(vmin=diff.min(), vcenter=0, vmax=diff.max())

            plt.imshow(diff.astype(int), cmap='bwr', norm=norm)
            plt.colorbar()
            plt.savefig(os.path.join(target_dir, k+'_diff.png'))

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

            extract_pickle_data(new_output_dict, _extract_target_dir(new_output))
            extract_pickle_data(reference_dict, _extract_target_dir(reference))
            compare_arrays(new_output_dict, reference_dict, _extract_target_dir(new_output))

            new_output_str = _data_to_str(new_output_dict)
            reference_str = _data_to_str(reference_dict)

            # sys.stdout.writelines(unified_diff(new_output_str, reference_str))
            diff_fd.writelines(unified_diff(new_output_str, reference_str))

    diff_fd.close()

    return f'Inconsistency in {new_output} compared to the reference data. ' \
           f'The diff can be seen above and is stored in {diff_fn}.'

def perform_dpre_ref_test(runner, params_fn, dataprep_only=True):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    params = params_fn()

    try:
        runner = runner()
        runner.set_options(params)
        if dataprep_only:
            # run only data preparation
            runner.set_comptype(CompType.dpre)
        runner.run()
    except ProviderError as e:
        sys.exit(e)

    if dataprep_only:
        dataprep_filepath = os.path.join(output_dir, 'dpre.save')
        reference_filepath = os.path.join(
            output_dir, '..', 'reference', 'gistest',
            'arcgis' if isinstance(runner, ArcGisRunner) else 'grass',
            'dpre.save')
        assert filecmp.cmp(dataprep_filepath, reference_filepath),\
            report_pickle_difference(dataprep_filepath, reference_filepath)
