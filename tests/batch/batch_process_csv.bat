@echo off

call "%~dp0\init_windows_env.bat"

rem change current directory to smpdepr2d root directory
cd /d %SMODERP2D_PATH%

rem install r.hydrodem
call grass%GRASS_VERSION% --tmp-location EPSG:5514 --exec g.extension extension=r.hydrodem

rem run batch process
python3 %SMODERP2D_PATH%\bin\grass\batch_process_csv.py ^
        --csv .\tests\batch\batch_process.csv ^
        --workers 1

rem wait for 5 sec
timeout /t 5
