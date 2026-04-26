@echo off
setlocal
cd /d "%~dp0"
title FRIDAY V8 - INSTALL / REPAIR

echo ======================================================
echo              FRIDAY V8 INSTALL / REPAIR
echo ======================================================
echo This will create a local .venv folder and install packages.
echo Keep internet ON for first setup.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PY=py -3
) else (
    set PY=python
)

%PY% --version
if errorlevel 1 (
    echo.
    echo Python not found. Install Python 3.12 from python.org and tick Add Python to PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ======================================================
echo INSTALL COMPLETE.
echo Next: run SELECT_MIC once, then START_FRIDAY.
echo Daily use: only double-click START_FRIDAY.
echo ======================================================
pause
