@echo off
cd /d "%~dp0"
title FRIDAY V8 - TEXT MODE
if not exist ".venv\Scripts\python.exe" call INSTALL.bat
".venv\Scripts\python.exe" friday.py --text
pause
