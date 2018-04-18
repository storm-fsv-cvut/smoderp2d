#!/bin/bash

d=`date -I`-smoderp2d



./bash/rmpyc.sh



zip -r $d.zip  smoderp2d tests setup.py



# tar -czf ../$d.tgz  *.py   main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/*.py main_src/main_classes/*.py 
# rsync -ave ssh ../$d.tgz jerabek@oldstorm.fsv.cvut.cz:/home/jerabek/smoderp_tar


