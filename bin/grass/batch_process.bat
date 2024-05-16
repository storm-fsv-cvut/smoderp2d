echo off

call C:\OSGeo4W\bin\o4w_env.bat
set pwd=%~dp0
set PYTHONPATH=%pwd%\..\..

cd /d %pwd%/../..
python3 %pwd%\batch_process.py ^
        --elevation .\tests\data\nucice\dem.tif ^
        --soil .\tests\data\nucice\soils.shp ^
        --soil_type_fieldname Soil ^
        --vegetation .\tests\data\nucice\landuse.shp  ^
        --vegetation_type_fieldname LandUse ^
        --rainfall_file .\tests\data\rainfall_nucice.txt ^
        --end_time 5 ^
        --maxdt 5 ^
        --table_soil_vegetation .\tests\data\nucice\soil_veg_tab.dbf ^
        --table_soil_vegetation_fieldname soilveg ^
        --output  %userprofile%\downloads\smoderp2d ^
        --points .\tests\data\nucice\points.shp ^
        --points_fieldname point_id ^
        --streams .\tests\data\nucice\streams.shp ^
        --channel_properties_table .\tests\data\nucice\streams_shape.dbf ^
        --streams_channel_type_fieldname channel_id ^
        --flow_direction 'single' ^
        --wave kinematic ^
        --generate_temporary

timeout /t 10