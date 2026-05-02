@echo off
title Install Friday Fast Wake Startup

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set FILE=%STARTUP%\Friday Fast Wake Listener.bat

echo Creating startup wake listener...
echo @echo off > "%FILE%"
echo cd /d "C:\FridayV8" >> "%FILE%"
echo start "Friday Fast Wake Listener" cmd /k "START_FRIDAY_FAST_WAKE.bat" >> "%FILE%"

echo.
echo Done. Wake listener will start when laptop starts.
echo File created:
echo %FILE%
echo.
pause
