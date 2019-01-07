v.import input=/home/martin/geodata/smoderp/original layer=puda output=puda -o
v.import input=/home/martin/geodata/smoderp/original layer=points2 output=points2 -o
v.import input=/home/martin/geodata/smoderp/original layer=tok output=tok -o
r.import input=/home/martin/geodata/smoderp/original/raster10m/w001001.adf output=w001001 -o
db.in.ogr input=/home/martin/geodata/smoderp/original/tabulkytab.dbf
db.select table=tabulkytab_dbf
db.in.ogr input=/home/martin/geodata/smoderp/original/tab_stream_tvar.dbf
g.gisenv
g.gisenv
