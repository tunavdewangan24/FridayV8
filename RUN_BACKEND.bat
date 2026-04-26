@echo off
cd /d "%~dp0backend"
if not exist ".env" (
    copy ".env.example" ".env"
    echo.
    echo Created backend\.env
    echo IMPORTANT: Open backend\.env and change owner email/password before public use.
    echo.
)
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
