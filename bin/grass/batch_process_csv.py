#!/usr/bin/env python3

import sys
import argparse
import csv

from smoderp2d.exceptions import ProviderError, MaxIterationExceeded

from batch_process import run_process

def get_params_epsg(params):
    epsg = params.pop('epsg')

    return params, int(epsg)

def run_process_single(params, epsg):
    # run single process
    print('-' * 80)
    print(f'Run process with {params}...')
    print('-' * 80)

    return run_process(params, epsg)

def main(csv_file, workers):
    # collect params
    params = []
    with open(csv_file, newline='') as fd:
        reader = csv.DictReader(fd, delimiter=';')
        for row in reader:
            if row['epsg'].startswith('#'):
                # skip commented rows
                continue
            for k, v in row.items():
                if v in ('true', 'false'):
                    row[k] = True if v.lower() == 'true' else False
            params.append(row)

    # check for duplicated output paths
    output_paths = set(p['output'] for p in params)
    if len(params) != len(output_paths):
        sys.exit("ERROR: Duplicated output paths detected")

    # run processes
    if workers > 1:
        from joblib import Parallel, delayed

        Parallel(n_jobs=workers, backend="multiprocessing", verbose=10)(
            delayed(run_process_single)(*get_params_epsg(p)) for p in params
        )
    else:
        for p in params:
            run_process_single(*get_params_epsg(p))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='batch_process_csv',
        description='Run SMODERP2D as batch processes from CSV',
        epilog=r'Usage: PYTHONPATH=`pwd` python3 bin/grass/batch_process_csv.py --csv \ bin/grass/batch_process.csv'
    )

    parser.add_argument('--csv', required=True)
    parser.add_argument('--workers', default=1)

    args = parser.parse_args()
    
    main(args.csv, int(args.workers))
