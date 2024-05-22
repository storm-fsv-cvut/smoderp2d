@echo off

call "C:\OSGeo4W\bin\o4w_env.bat"
set GRASS_VERSION=83

rem set GRASS GIS environment
call "%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\etc\env.bat"
path %OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\lib;%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\bin;%PATH%

rem add smoderp2d root directory to python path
set SMODERP2D_PATH=%~dp0\..\..
set PYTHONPATH=%SMODERP2D_PATH%;%PYTHONPATH%

