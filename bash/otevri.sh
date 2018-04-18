#!/bin/bash

echo
echo '<a> joo / <cokolivek> nee otevrit kate:'
echo
read a
if [ "$a" == "a" ] ; then
  kate -n a.in &
  sleep 0.5
  kate -n smoderp2d/src/data_preparation.py smoderp2d/*.py smoderp2d/src/runoff.py smoderp2d/src/courant.py smoderp2d/src/time_step.py  bash/otevri.sh bash/zabal.sh smoderp2d/src/main_classes/*.py smoderp2d/src/io_functions/*.py smoderp2d/src/tools/*.py smoderp2d/src/stream_functions/*.py smoderp2d/src/processes/*.py smoderp2d/src/main_classes/*.py  smoderp2d/src/*.py &
fi



