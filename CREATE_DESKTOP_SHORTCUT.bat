@echo off
cd /d "%~dp0"
title FRIDAY V8 - CREATE DESKTOP SHORTCUT
set "VBS=%TEMP%\create_friday_v5_shortcut.vbs"
> "%VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\FRIDAY V8.lnk"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%~dp0START_FRIDAY.bat"
>> "%VBS%" echo oLink.WorkingDirectory = "%~dp0"
>> "%VBS%" echo oLink.Description = "Start FRIDAY V8 Universal Windows Control"
>> "%VBS%" echo oLink.Save
cscript //nologo "%VBS%"
del "%VBS%" >nul 2>nul
echo Desktop shortcut created: FRIDAY V8
pause
