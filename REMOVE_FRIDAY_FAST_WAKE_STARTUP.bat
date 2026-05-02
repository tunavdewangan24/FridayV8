@echo off
title Remove Friday Fast Wake Startup

set FILE=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Friday Fast Wake Listener.bat

if exist "%FILE%" (
    del "%FILE%"
    echo Removed startup wake listener.
) else (
    echo Startup wake listener not found.
)

pause
