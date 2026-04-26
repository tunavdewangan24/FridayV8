@echo off
cd /d "%~dp0"
title FRIDAY V8 - MICROPHONE TEST
if not exist ".venv\Scripts\python.exe" call INSTALL.bat
".venv\Scripts\python.exe" mic_test.py
pause
