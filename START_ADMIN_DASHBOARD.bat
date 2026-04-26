@echo off
cd /d "%~dp0admin_dashboard"
python -m http.server 8080
pause
