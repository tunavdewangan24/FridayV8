FridayV8 Backend Fix

Problem:
The backend may fail with:
"module 'bcrypt' has no attribute '__about__'"
or
"ValueError: password cannot be longer than 72 bytes"

Reason:
passlib 1.7.4 has compatibility issues with bcrypt 5.0.0.

Fix:
Use bcrypt==4.0.1.

Easy method:
Double-click FIX_BCRYPT_AND_RUN_BACKEND.bat

Manual method:
python -m pip uninstall -y bcrypt
python -m pip install bcrypt==4.0.1
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
