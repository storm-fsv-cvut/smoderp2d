#!/bin/bash

d=`date -I`-smoderp-core

echo Toto balis:

echo
ls -ld main_src/flow_algorithm/
ls -l main_src/flow_algorithm/*.py

echo
ls -ld main_src/stream_functions/
ls -l main_src/stream_functions/*.py

echo
ls -ld  main_src/io_functions/
ls -l   main_src/io_functions/*.py

echo
ls -ld  main_src/tools/
ls -l   main_src/tools/*.py

echo
ls -ld  main_src/processes/
ls -l   main_src/processes/*.py


echo
ls -ld  main_src/main_classes/
ls -l   main_src/main_classes/*.py


echo
ls -ld  main_src/
ls -l   main_src/*.py


echo
echo
ls -ld ./
ls -l *.py


echo Enter joo / ^C nee:
read 

tar -czf ../$d.tgz  *.py   main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/*.py main_src/main_classes/*.py 
rsync -ave ssh ../$d.tgz jerabek@oldstorm.fsv.cvut.cz:/home/jerabek/smoderp_tar


