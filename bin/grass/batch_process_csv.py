#!/usr/bin/env python3

import argparse
import csv
from joblib import Parallel, delayed 

from batch_process import run_process

def get_params_epsg(params):
    epsg = params.pop('epsg')

    return params, int(epsg)

def main(csv_file, workers):
    # collect params
    params = []
    with open(csv_file, newline='') as fd:
        reader = csv.DictReader(fd)
        for row in reader:
            if row['epsg'].startswith('#'):
                # skip commented rows
                continue
            for k, v in row.items():
                if v in ('true', 'false'):
                    row[k] = True if v.lower() == 'true' else False
            params.append(row)
            print(row)

    # run processes
    Parallel(n_jobs=workers, backend="multiprocessing", verbose=10)(
        delayed(run_process)(*get_params_epsg(param)) for param in params
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='batch_process_csv',
        description='Run SMODERP2D as batch processes in parallel'
    )

    parser.add_argument('--csv', required=True)
    parser.add_argument('--workers', default=1)

    args = parser.parse_args()
    
    main(args.csv, int(args.workers))
    # main(args.csv)
