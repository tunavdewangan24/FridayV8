@echo off
title Friday Fast Voice
cd /d "C:\FridayV8"

echo Starting Friday Fast Voice Mode...
python -c "import FRIDAY_FAST_MODE as f; f.voice_mode()"

pause
