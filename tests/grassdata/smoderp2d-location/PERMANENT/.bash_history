v.import input=/home/martin/geodata/smoderp/original layer=puda output=puda -o
v.import input=/home/martin/geodata/smoderp/original layer=points2 output=points2 -o
v.import input=/home/martin/geodata/smoderp/original layer=tok output=tok -o
r.import input=/home/martin/geodata/smoderp/original/raster10m/w001001.adf output=w001001 -o
db.in.ogr input=/home/martin/geodata/smoderp/original/tabulkytab.dbf
db.select table=tabulkytab_dbf
db.in.ogr input=/home/martin/geodata/smoderp/original/tab_stream_tvar.dbf
g.gisenv
g.gisenv
db.in.ogr input=/home/martin/geodata/smoderp/original/tab_stream_tvar.dbf
v.import input=tests/data/ layer=tok output=tok -o
v.import input=tests/data/ layer=tok output=tok -o --o
db.select tab_stream_tvar
db.select tab=tab_stream_tvar
db.in.ogr input=/home/martin/geodata/smoderp/original/tab_stream_tvar.dbf table=tab_stream_tvar
db.in.ogr input=/home/martin/geodata/smoderp/original/tab_stream_tvar.dbf output=tab_stream_tvar  --o
db.select tab=tab_stream_tvar
db.in.ogr input=tests/data/tab_stream_tvar.dbf output=tab_stream_tvar  --o
db.select tab=tab_stream_tvar
db.select tab=tok
