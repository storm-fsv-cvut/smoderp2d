import os
import sys
import filecmp

from smoderp2d.exceptions import ProviderError
from smoderp2d.providers.base import CompType

data_dir = os.path.join(os.path.dirname(__file__), "data")
output_dir = os.path.join(data_dir, "output")

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
    ) == True
