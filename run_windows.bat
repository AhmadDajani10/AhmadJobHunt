@echo off
cd /d "%~dp0"
set "PY="

rem 1) the "py" launcher that python.org installs
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"

rem 2) a standard per-user install, e.g. C:\Users\you\AppData\Local\Programs\Python\Python312
if not defined PY (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PY="%%D\python.exe""
  )
)

rem 3) whatever "python" is on PATH
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)

if not defined PY (
  echo Could not find Python. Install it from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo Using Python: %PY%
%PY% hunt.py %*
echo.
pause
