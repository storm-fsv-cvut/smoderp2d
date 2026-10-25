@echo off

call "%~dp0\init_windows_env.bat"

python3 -m pip install joblib

rem wait for 5 sec
timeout /t 5