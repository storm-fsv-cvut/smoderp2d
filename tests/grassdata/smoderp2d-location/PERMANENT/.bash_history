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
g.list raster 
g.list raster 
g.remove 
g.remove type=raster name=w001001 -f
ls
rm -rf tests/grassdata/smoderp2d-location/stream_prep/
g.remove type=raster name=w001001 -f
g.list rast
g.list vect
g.remove vect=soils_LU
g.remove name=soils_LU type=vect
g.remove name=soils_LU type=vector
g.remove name=soils_LU type=vector
g.list vect
g.remove name=soil_LU type=vector
g.remove name=soil_LU type=vector -f
ogrinfo soils
ogrinfo soils.shp
ogrinfo soils.shp -al
v.import in=soils.shp 
v.import in=soils.shp -o --o
v.import in=landuse.shp -o --o
db.tables 
db.drop table=soil_LU_property
db.droptable table=soil_LU_property
db.droptable table=soil_LU_property -f
db.in.ogr in=soil_veg_tab_mean.dbf 
db.select table=soil_veg_tab_mean_dbf
db.in.ogr in=soil_veg_tab_mean.dbf out=soil_veg_tab_mean
db.in.ogr in=tests/data/soil_veg_tab_mean.dbf out=soil_veg_tab_mean
