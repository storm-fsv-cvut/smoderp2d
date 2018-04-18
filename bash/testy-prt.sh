#!/bin/bash


dir_=`ls -d test-out/*/*.dat`
dir_=`ls -d test-out/*/`

r='/'
mkdir -p test-png

for d in $dir_
do

  f=`ls -d $d*.dat`
  echo set terminal png                  >  test-png/plot.gplot
  tm=${d//[$r]/_}.png
  echo set output "'"test-png/$tm"'"     >>  test-png/plot.gplot
  echo set datafile separator '"'\;'"'   >>  test-png/plot.gplot
  
  echo plot  \\   >>  test-png/plot.gplot
  
  for if_ in $f  
  do
    echo  "'"$if_"'" u 1:5 w l , \\           >>  test-png/plot.gplot
  done
  gnuplot < test-png/plot.gplot
done



