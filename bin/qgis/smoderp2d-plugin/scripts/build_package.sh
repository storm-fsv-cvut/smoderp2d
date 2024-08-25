#!/bin/bash -e

VENV=/tmp/smoderp2d_plugin
python3 -m venv $VENV
source $VENV/bin/activate

script_dir=$(realpath $(dirname $0))
echo $script_dir
# pip3 install smoderp2d
(cd ../../.. ;pip3 install .)

pv=$(python3 -V | cut -d' ' -f 2 | cut -d'.' -f 1,2)
LIB=$VENV/lib/python$pv/site-packages

pb_tool deploy -y -p zip_build/

plugin_dir=zip_build/smoderp2d_plugin
cp -r $LIB/smoderp2d $plugin_dir/
cp -r ../../base $plugin_dir/
find $plugin_dir/smoderp2d $plugin_dir/base -name __pycache__ | xargs rm -rf
for provider in 'arcgis' 'cmd' 'profile1d' 'wps'; do
    rm -rv $plugin_dir/smoderp2d/providers/$provider
    rm -rvf $plugin_dir/smoderp2d/runners/${provider}.py
done

patch zip_build/smoderp2d_plugin/smoderp_2D_dockwidget.py < patches/smoderp_2D_dockwidget.patch

(cd zip_build; zip -r smoderp2d_plugin.zip smoderp2d_plugin) # pb_tool zip will overwrite patched file

deactivate
rm -rf $VENV

exit 0
