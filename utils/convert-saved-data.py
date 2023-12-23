#!/usr/bin/env python

import sys
import os
import shutil
import argparse
import pickle

from smoderp2d.providers.base import BaseProvider


def main(filename):
    shutil.copyfile(filename, filename + '.orig')

    indata = load_data(filename)

    data = {
        'br': indata[0], 'bc': indata[1], 'mat_boundary': indata[2],
        'rr': indata[3], 'rc': indata[4], 'outletCells': indata[5],
        'xllcorner': indata[6], 'yllcorner': indata[7],
        'NoDataValue': indata[8], 'array_points': indata[9],
        'c': indata[10], 'r': indata[11], 'combinatIndex': indata[12],
        'delta_t': indata[13], 'mat_pi': indata[14],
        'mat_ppl': indata[15], 'surface_retention': indata[16],
        'mat_inf_index': indata[17], 'mat_hcrit': indata[18],
        'mat_aa': indata[19], 'mat_b': indata[20],
        'mat_reten': indata[21], 'mat_fd': indata[22],
        'mat_dmt': indata[23], 'mat_effect_cont': indata[24],
        'mat_slope': indata[25], 'mat_nan': indata[26],
        'mat_a': indata[27], 'mat_n': indata[28],
        'outdir': indata[29], 'pixel_area': indata[30],
        'points': indata[31], 'poradi': indata[32],
        'end_time': indata[33], 'spix': indata[34],
        'state_cell': indata[35], 'temp': indata[36],
        'type_of_computing': indata[37], 'vpix': indata[38],
        'mfda': indata[39], 'sr': indata[40], 'itera': indata[41],
        'toky': indata[42], 'cell_stream': indata[43],
        'mat_tok_reach': indata[44], 'STREAM_RATIO': indata[45],
        'toky_loc': indata[46]
    }

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
