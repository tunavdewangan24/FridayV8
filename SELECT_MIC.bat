@echo off
cd /d "%~dp0"
title FRIDAY V8 - SELECT MICROPHONE
if not exist ".venv\Scripts\python.exe" call INSTALL.bat
".venv\Scripts\python.exe" select_mic.py
pause
