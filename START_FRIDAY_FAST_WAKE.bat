@echo off
title Friday Fast Wake Listener
cd /d "C:\FridayV8"

echo Installing required packages if missing...
python -m pip install SpeechRecognition pyaudio pyautogui pyperclip pyttsx3 >nul 2>nul

python FRIDAY_FAST_WAKE.py
pause
