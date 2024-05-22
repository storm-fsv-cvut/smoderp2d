@echo off

rem define installation directory
set INSTALL_DIR=C:\OSGeo4W
rem set INSTALL_DIR=C:\Program Files\QGIS 3.36.2\

rem GRASS version
set GRASS_VERSION=83

rem set GRASS GIS environment
call "%INSTALL_DIR%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\etc\env.bat"
path %OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\lib;%OSGEO4W_ROOT%\apps\grass\grass%GRASS_VERSION%\bin;%PATH%

rem add smoderp2d root directory to python path
set SMODERP2D_PATH=%~dp0\..\..
set PYTHONPATH=%SMODERP2D_PATH%;%PYTHONPATH%

