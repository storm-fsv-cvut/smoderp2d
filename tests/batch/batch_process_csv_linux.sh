#!/bin/sh

# install r.hydrodem
grass --tmp-location EPSG:5514 --exec g.extension extension=r.hydrodem

# run batch process
PYTHONPATH=`pwd` python3 ./bin/grass/batch_process_csv.py \
          --csv ./tests/batch/batch_process.csv \
          --workers 1
