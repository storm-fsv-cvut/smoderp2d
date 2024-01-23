#!/bin/bash -e

VENV=/tmp/smoderp2d_plugin
python3 -m venv $VENV
source $VENV/bin/activate

script_dir=$(realpath $(dirname $0))
echo $script_dir
pip3 install $script_dir/../../../../ # root directory

LIB=$VENV/lib/python3.11/site-packages
rm -rf ./smoderp2d
cp -r $LIB/smoderp2d .
find smoderp2d -name __pycache__ | xargs rm -rf
for provider in 'arcgis' 'cmd' 'profile1d' 'wps'; do
    rm -rv ./smoderp2d/providers/$provider
    rm -rvf ./smoderp2d/runners/${provider}.py
done

pb_tool zip

deactivate
rm -rf $VENV

exit 0
