@echo off
REM OPTION 1 - QGIS installed using OSGeo4W Network installer
call "C:\OSGeo4W64\bin\o4w_env.bat"
REM OPTION 2 - QGIS installed using Standalone installer
REM call "C:\Program Files\QGIS 3.16\bin\o4w_env.bat"

call py3_env.bat

@echo off

cd /d ..
"%PYTHONHOME%\python" bin/start-nogis-smoderp2d.py --config tests/nogis.ini

pause
