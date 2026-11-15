@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 hunt.py %*) else (python hunt.py %*)
echo.
pause
