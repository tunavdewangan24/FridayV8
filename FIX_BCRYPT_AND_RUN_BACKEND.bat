@echo off
echo Fixing bcrypt compatibility for FridayV8 backend...
python -m pip uninstall -y bcrypt
python -m pip install bcrypt==4.0.1
echo.
echo Starting FridayV8 backend...
cd /d "%~dp0backend"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
