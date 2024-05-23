#!/usr/bin/env python3

import argparse
import csv

from batch_process import run_process

from smoderp2d.core.general import Globals, GridGlobals

def get_params_epsg(params):
    epsg = params.pop('epsg')

    return params, int(epsg)

def run_process_single(params, epsg):
    # run single process
    print('-' * 80)
    print(f'Run process with {params}...')
    print('-' * 80)
    run_process(params, epsg)
    # reset global variables
    Globals.reset()
    GridGlobals.reset()

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
