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
        'mat_b': indata[19], 'mat_reten': indata[20], 'mat_fd': indata[21],
        'mat_dmt': indata[22], 'mat_effect_cont': indata[23],
        'mat_slope': indata[24], 'mat_nan': indata[25], 'mat_a': indata[26],
        'mat_n': indata[27], 'outdir': indata[28], 'pixel_area': indata[29],
        'points': indata[30], 'poradi': indata[31], 'end_time': indata[32],
        'spix': indata[33], 'state_cell': indata[34], 'temp': indata[35],
        'type_of_computing': indata[36], 'vpix': indata[37],
        'mfda': indata[38], 'sr': indata[39], 'itera': indata[40],
        'toky': indata[41], 'cell_stream': indata[42],
        'mat_tok_reach': indata[43], 'STREAM_RATIO': indata[44],
        'toky_loc': indata[45]
    }

    BaseProvider.save_data(data, filename)


def load_data(filename):
    """Load data from pickle.

    :param str filename: file to be loaded
    """
    with open(filename, 'rb') as fd:
        data = pickle.load(fd, encoding='bytes')

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
