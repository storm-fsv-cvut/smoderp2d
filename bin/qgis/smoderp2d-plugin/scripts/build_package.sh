#!/bin/bash -e

# create virtual environment
VENV=/tmp/smoderp2d_plugin
python3 -m venv $VENV
source $VENV/bin/activate

script_dir=$(realpath $(dirname $0))
echo $script_dir
### install released SMODERP2D version
# pip3 install smoderp2d
### or from git
(cd ../../.. ;pip3 install .)

pv=$(python3 -V | cut -d' ' -f 2 | cut -d'.' -f 1,2)
LIB=$VENV/lib/python$pv/site-packages

# create zip
pb_tool deploy -y -p zip_build/

plugin_name=smoderp2d_plugin
plugin_dir=zip_build/$plugin_name
cp -r $LIB/smoderp2d $plugin_dir/
cp -r ../../base $plugin_dir/

# remove files and dirs that are unnecessary in the plugin
find $plugin_dir/smoderp2d $plugin_dir/base -name __pycache__ | xargs rm -rf
for provider in 'arcgis' 'cmd' 'profile1d' 'wps'; do
    rm -rv $plugin_dir/smoderp2d/providers/$provider
    rm -rvf $plugin_dir/smoderp2d/runners/${provider}.py
done

# apply patch
patch zip_build/${plugin_name}/smoderp_2D_dockwidget.py < patches/smoderp_2D_dockwidget.patch

# copy LICENSE file
cp ../../../LICENSE zip_build/${plugin_name}/

(cd zip_build; zip -r ${plugin_name}.zip ${plugin_name}) # pb_tool zip will overwrite patched file

deactivate
rm -rf $VENV

exit 0
