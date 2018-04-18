#!/bin/bash

d=`date -I`-smoderp

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
ls -ld  rscripty
ls -l   rscripty/


echo
ls -ld  obr
ls -l   obr/

echo
ls -ld  indata
ls -l   indata/



echo
ls -ld  bash
ls -l   bash/*.sh

echo
echo
ls -ld ./
echo
ls -l *.py
echo
ls -l 
echo
ls -l *.doxyconf
echo

ls -ld  stare_src/
ls -l   stare_src/
echo

echo Enter joo / ^C nee:
read 

tar -czf ../$d.tgz a.sh b.sh *.py  bash/*.sh *.doxyconf main_src/flow_algorithm/*.py main_src/stream_functions/*.py main_src/io_functions/*.py  main_src/tools/*.py main_src/processes/*.py main_src/*.py main_src/main_classes/*.py rscripty obr stare_src indata
rsync -ave ssh ../$d.tgz jerabek@oldstorm.fsv.cvut.cz:/home/jerabek/smoderp_tar


