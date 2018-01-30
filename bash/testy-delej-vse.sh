

# vyroby indat podle techto dvou listu

smodskript=start-smoderp2d.py

data=(trych01 trych02 trych05 trych01dist konk01 konv01)
srazka=(krabice-mala krabice-velka pulz trojuhelnik velbloud)

function soubor {

echo [GIS]   > $1
echo dem: C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\1_rst\\ds_plocha      >> $1
echo soil: C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\2_vect\\plocha.shp   >> $1
echo lu: C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\2_vect\\plocha.shp     >> $1
echo                     >> $1
echo [shape atr]         >> $1
echo soil-atr: puda      >> $1
echo lu-atr: LU          >> $1
echo                     >> $1
echo [srazka]            >> $1
echo file: bash/test-in/sr-$2.txt >> $1
echo                   >> $1
echo [time]            >> $1
echo \#min             >> $1
echo maxdt: 20         >> $1
echo \#min             >> $1
echo endtime: 1       >> $1
echo                   >> $1
echo [Other]    >> $1
echo reten: 0.0 >> $1
echo points: C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\2_vect\\point2.shp  >> $1
echo outdir: bash/test-out/out-$3-$2                                           >> $1
echo typecomp: 3                                            >> $1
echo mfda: False                                            >> $1
echo soilvegtab : C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\3_tabs\\tabulkytab.dbf    >> $1
echo soilvegcode : SOILVEG                                                                     >> $1
echo streamshp :  C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\2_vect\\toky.shp          >> $1
echo streamtab: C:\Users\jerabj11\Desktop\\4_DS_plocha\\1_data_in\\3_tabs\\tab_stream_tvar.txt >> $1
echo streamtabcode: smoderp >> $1
echo arcgis: False          >> $1
echo extraout: False        >> $1
echo indata: indata/$3.save >> $1
echo partialcomp: roff      >> $1
echo debugprt: True         >> $1
echo printtimes: -          >> $1

}


echo ${data[*]}
echo ${srazka[*]}

for id in ${data[*]}; do
  for is in ${srazka[*]}; do
    echo bash/test-in/$id-$is.in
    soubor bash/test-in/$id-$is.in $is $id
  done
done



echo \# TENTO SOUBOR SE GENERUJE AUTOMATICKY V bash/testy-delej-vse.sh > bash/testy-run.sh
echo >>  bash/testy-run.sh
for id in ${data[*]}; do
  for is in ${srazka[*]}; do
    echo python $smodskript --indata bash/test-in/$id-$is.in roff \> bash/test-out/$id-$is.log >> bash/testy-run.sh
  done
done
