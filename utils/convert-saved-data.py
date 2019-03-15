#!/usr/bin/env python

import sys
import os
import shutil
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from smoderp2d.tools.save_load_data import load_data, save_data

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
        data['spix'],                     \
        data['state_cell'],               \
        data['temp'],                     \
        data['type_of_computing'],        \
        data['vpix'],                     \
        data['mfda'],                     \
        data['sr'],                       \
        data['itera'],                    \
        data['toky'],                     \
        data['cell_stream'],              \
        data['mat_tok_reach'],            \
        data['STREAM_RATIO'],             \
        data['toky_loc'] = indata

    save_data(data, filename)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert saved data.')

    parser.add_argument('--data',
                        metavar='FILE',
                        type=str,
                        required=True,
                        help='input saved data file')
    args = parser.parse_args()
    
    sys.exit(main(args.data))
