@echo off

call "C:\OSGeo4W\bin\o4w_env.bat"
set GRASS_VERSION=83

rem set GRASS GIS environment
call "%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\etc\env.bat"
path %OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\lib;%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\bin;%PATH%

rem add smoderp2d root directory to python path
set smoderp2d_path=%~dp0\..\..
set PYTHONPATH=%smoderp2d_path%;%PYTHONPATH%
echo %PYTHONPATH%

rem change current directory to smpdepr2d root directory
cd /d %smoderp2d_path%

rem run batch process
python3 %~dp0%\batch_process_csv.py ^
        --csv .\tests\batch\batch_process.csv

rem wait for 5 sec
timeout /t 5
