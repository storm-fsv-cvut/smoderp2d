#!/bin/bash

d=`date -I`-jj

echo Toto publikujes:

echo
ls -ld smoderp2d/src/flow_algorithm/
ls -l smoderp2d/src/flow_algorithm/*.py

echo
ls -ld smoderp2d/src/stream_functions/
ls -l smoderp2d/src/stream_functions/*.py

echo
ls -ld  smoderp2d/src/io_functions/
ls -l   smoderp2d/src/io_functions/*.py

echo
ls -ld  smoderp2d/src/tools/
ls -l   smoderp2d/src/tools/*.py


echo
ls -ld  smoderp2d/src/processes/
ls -l   smoderp2d/src/processes/*.py

echo
ls -ld  smoderp2d/src/main_classes/
ls -l   smoderp2d/src/main_classes/*.py

echo
ls -ld  smoderp2d/src/
ls -l   smoderp2d/src/*.py


echo
echo
ls -ld ./
echo
ls -l main.py
echo

echo /home/nazvpr/smoderp_verze/$d
echo Enter joo / ^C nee:
read 


echo "Chci dopsat komentari k archyvu?"
echo "JOO - [popis] <enter>"
echo "NEE - <enter>"

read text

if [ -n "$text" ]; then
  echo `date` > info.log
  echo $text >> info.log
fi




ssh storm "mkdir -p /home/nazvpr/smoderp_verze/$d"
rsync -Rave ssh info.log *.py smoderp2d/*.py smoderp2d/src/flow_algorithm/*.py smoderp2d/src/stream_functions/*.py smoderp2d/src/io_functions/*.py  smoderp2d/src/tools/*.py smoderp2d/src/processes/*.py smoderp2d/src/main_classes/*.py smoderp2d/src/*.py storm:/home/nazvpr/smoderp_verze/$d

if [ -n "$text" ]; then
  rm info.log
fi
