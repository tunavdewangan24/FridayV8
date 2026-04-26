@echo off
cd /d "%~dp0"
title FRIDAY V8 - UNIVERSAL WINDOWS CONTROL
if not exist ".venv\Scripts\python.exe" call INSTALL.bat
".venv\Scripts\python.exe" friday.py --voice
pause
