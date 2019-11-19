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
g.remove type=raster name=w001001 -f
g.mapset -p
mc tests/grassdata/smoderp2d-location/PERMANENT/
g.list raster 
ls tests/data/
r.in.gdal in=tests/data/dem10m/ out=dem10m
r.in.gdal in=tests/data/dem10m/ out=dem10m -o
r.info dem10m
g.gui
r.info dem10m
g.list vect
g.remove type=vect name=points2 -f
v.import in=tests/data/points.shp out=points 
v.import in=tests/data/points.shp out=points -o
v.info points
v.info points -v
v.info points -c
ls tests/data/
g.list vect
g.remove type=vect name=puda -f
g.list vect
v.import in=tests/data/soil_LU.shp out=soil_LU -o
v.info soil_LU
v.info soil_LU -c
v.db.select soil_LU 
v.db.select points
g.list vect
g.remove type=vect name=tok -f
v.import in=tests/data/stream.shp out=stream -o
v.db.select stream
g.list rast
g.list vect
g.list rast
v.db.select soil_LU 
ls tests/data/
v.db.select soil_LU 
db.tables 
g.mapset -p
db.droptable 
db.droptable table=tab_stream_tvar
db.droptable table=tab_stream_tvar -f
db.droptable table=tab_stream_tvar_dbf -f
db.tables 
db.droptable table=tabulkytab -f
db.tables 
ls tests/data/
ls tests/data/*.dbf
db.in.ogr in=tests/data/soil_LU_property.dbf out=soil_LU_property
db.select table=soil_LU_property
db.in.ogr in=tests/data/stream_shape.dbf out=stream_shape
db.select table=stream_shape
ls tests/data/*.dbf
ls tests/data/
ls tests/data/*.txt
db.select table=stream_shape
db.select table=soil_LU_property
db.select table=soil_LU_property
db.select table=stream_shape
db.select table=soil_LU
db.select table=stream_shape
db.select table=soil_LU_property
git status
db.in.ogr in=tests/data/soil_LU_property.dbf out=soil_LU_property
db.in.ogr in=tests/data/soil_LU_property.dbf out=soil_LU_property --o
db.select table=soil_LU_property
git status
v.import in=tests/data/stream.shp out=stream -o
v.import in=tests/data/stream.shp out=stream -o --o
v.db.select soil_LU 
v.db.select stream
git status
mv nan.diff ..
git status
git add .
git commit -am"update QGIS project and GRASS usage to test data in English, see #61"
git push
g.list vect
python
python3
