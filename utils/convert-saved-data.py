#!/usr/bin/env python3

import sys
import os
import shutil
import argparse
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d.providers.base import BaseProvider


def main(filename):
    shutil.copyfile(filename, filename + '.orig')

    indata = load_data(filename)

    data = {}
    data['br'],                       \
        data['bc'],                       \
        data['mat_boundary'],             \
        data['rr'],                       \
        data['rc'],                       \
        data['outletCells'],              \
        data['xllcorner'],                \
        data['yllcorner'],                \
        data['NoDataValue'],              \
        data['array_points'],             \
        data['c'],                        \
        data['r'],                        \
        data['combinatIndex'],            \
        data['delta_t'],                  \
        data['mat_pi'],                   \
        data['mat_ppl'],                  \
        data['surface_retention'],        \
        data['mat_inf_index'],            \
        data['mat_hcrit'],                \
        data['mat_aa'],                   \
        data['mat_b'],                    \
        data['mat_reten'],                \
        data['mat_fd'],                   \
        data['mat_dmt'],                  \
        data['mat_efect_cont'],           \
        data['mat_slope'],                \
        data['mat_nan'],                  \
        data['mat_a'],                    \
        data['mat_n'],                    \
        data['outdir'],                   \
        data['pixel_area'],               \
        data['points'],                   \
        data['poradi'],                   \
        data['end_time'],                 \
        data['state_cell'],               \
        data['temp'],                     \
        data['type_of_computing'],        \
        data['mfda'],                     \
        data['sr'],                       \
        data['itera'],                    \
        data['toky'],                     \
        data['cell_stream'],              \
        data['mat_tok_reach'],            \
        data['STREAM_RATIO'],             \
        data['toky_loc'] = indata

    BaseProvider._save_data(data, filename)


def load_data(filename):
    """Load data from pickle.

    :param str filename: file to be loaded
    """
    with open(filename, 'rb') as fd:
        if sys.version_info > (3, 0):
            data = pickle.load(fd, encoding='bytes')
        else:
            data = pickle.load(fd)

    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert saved data.')

    parser.add_argument('--data',
                        metavar='FILE',
                        type=str,
                        required=True,
                        help='input saved data file')
    args = parser.parse_args()

    sys.exit(main(args.data))
