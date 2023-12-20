#!/bin/sh

if test -z "$1"; then
    echo "Usage: $0 quicktest|test"
    exit 1
fi

settings=("sheet" "rill" "sheet_stream" "rill_mfda" "stream_rill")

for setting in ${settings[*]}
do
  echo "tests/data/reference/${1}_${setting}"
  rm -r tests/data/reference/${1}_${setting}/*
  pytest tests/test_cmd.py --config config_files/${1}_${setting}.ini
  cp -r tests/data/output/* tests/data/reference/${1}_${setting}/
done