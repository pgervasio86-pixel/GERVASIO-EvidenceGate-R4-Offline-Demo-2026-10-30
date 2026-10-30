@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 src\run_live_once.py
) else (
  python src\run_live_once.py
)
