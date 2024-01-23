#!/bin/sh

if test -z "$1"; then
    echo "Usage: $0 quicktest|test|gistest|profile1d"
    exit 1
fi


if [[ "$1" == gistest ]]; then
	settings=("rain_sim" "nucice")
	for setting in ${settings[*]}
	do
	  echo "tests/data/reference/${1}_${setting}"
	  rm -r tests/data/reference/${1}_${setting}/*/*
	  ./tests/run_grass_gistest.sh $setting dpre
	  cp -r tests/data/output/* tests/data/reference/${1}_${setting}/dpre/
	  cp -r tests/data/reference/${1}_${setting}/dpre/dpre.save tests/data/${setting}.save
	  ./tests/run_grass_gistest.sh $setting
	  cp -r tests/data/output/* tests/data/reference/${1}_${setting}/full/
	done
elif [[ "$1" == profile1d ]]; then
	echo "tests/data/reference/profile1d"
	rm -r tests/data/reference/profile1d/*
	pytest tests/test_profile1d.py
	cp -r tests/data/output/* tests/data/reference/profile1d/
else
	settings=("sheet" "rill" "sheet_stream" "stream_rill")
	for setting in ${settings[*]}
	do
	  echo "tests/data/reference/${1}_${setting}"
	  rm -r tests/data/reference/${1}_${setting}/*
	  pytest tests/test_cmd.py --config config_files/${1}_${setting}.ini
	  cp -r tests/data/output/* tests/data/reference/${1}_${setting}/
	done
	# do the quicktest/test different test (MFDA)
	if [[ "$1" == quicktest ]]; then
	  setting="rill_mfda"
        else
	  setting="stream_rill_mfda"
	fi
	echo "tests/data/reference/${1}_${setting}"
	rm -r tests/data/reference/${1}_${setting}/*
	pytest tests/test_cmd.py --config config_files/${1}_${setting}.ini
	cp -r tests/data/output/* tests/data/reference/${1}_${setting}/
fi
