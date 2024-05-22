#!/bin/sh

PYTHONPATH=`pwd` python3 ./bin/grass/batch_process_csv.py \
          --csv ./tests/batch/batch_process.csv \
          --workers 1
