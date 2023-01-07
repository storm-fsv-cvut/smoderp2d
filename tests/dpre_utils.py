import os
import sys
import pickle
import filecmp

from difflib import unified_diff

from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import CompType

data_dir = os.path.join(os.path.dirname(__file__), "data")
output_dir = os.path.join(data_dir, "output")


def report_pickle_difference(new_output, reference):
    """Report the inconsistency of two files.

    To be called when output comparison assert fails.

    :param new_output: path to the new output file
    :param reference: path to the reference file
    :return: string message reporting the content of the new output
    """
    sys.stdout.write('{} not consistent with '
                     'the stored results. The diff is as '
                     'follows:\n\n'.format(new_output))

    with open(new_output, 'rb') as left:
        with open(reference, 'rb') as right:
            if sys.version_info > (3, 0):
                new_output_dict = pickle.load(left, encoding='bytes')
                reference_dict = pickle.load(right, encoding='bytes')
            else:
                new_output_dict = pickle.load(left)
                reference_dict = pickle.load(right)

            new_output_str = [
                '%s:%s\n' % (key, value) for (key,  value) in sorted(
                    new_output_dict.items()
                )
            ]
            reference_str = [
                '%s:%s\n' % (key, value) for (key, value) in sorted(
                    reference_dict.items()
                )
            ]

            sys.stdout.writelines(unified_diff(new_output_str, reference_str))

    return 'Inconsistency in {}'.format(new_output)


def perform_dpre_ref_test(runner, params_fn):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    params = params_fn()

    try:
        runner = runner()
        runner.set_options(params)
        # run only data preparation
        runner.set_comptype(
            comp_type=CompType.dpre,
            data_file=params['pickle_file']
        )
        runner.run()
    except ProviderError as e:
        sys.exit(e)

    assert filecmp.cmp(
        params['pickle_file'],
        os.path.join(output_dir, '..', 'reference', 'dpre.save')
    ), report_pickle_difference(
        params['pickle_file'],
        os.path.join(output_dir, '..', 'reference', 'dpre.save')
    )
