# FridayV8 Secure Login + Database Edition

This is FridayV8 with:

- Desktop multitasking commands
- User account register/login
- Database-backed command history by email
- User history check later
- Owner/Author dashboard
- User suspension controls
- Maintenance mode
- Safety events
- Owner audit logs
- Privacy-first rules

## Folder Structure

```text
FridayV8-Secure-Login-Database/
├── friday.py
├── friday_api_client.py
├── login_setup.py
├── LOGIN_SETUP.bat
├── RUN_BACKEND.bat
├── START_FRIDAY.bat
├── START_TEXT_MODE.bat
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── .env.example
├── admin_dashboard/
│   └── index.html
├── website/
│   └── index.html
└── .github/workflows/build-windows.yml
```

## Local Testing Steps

### 1. Start the backend

Double-click:

```text
RUN_BACKEND.bat
```

The API will run at:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### 2. Register/Login user account

Double-click:

```text
LOGIN_SETUP.bat
```

Choose:

```text
1. Register new account
```

or:

```text
2. Login existing account
```

### 3. Start FridayV8

Double-click:

```text
START_TEXT_MODE.bat
```

or:

```text
START_FRIDAY.bat
```

Commands will be saved under the logged-in user's email.

### 4. User checks history

Run `LOGIN_SETUP.bat` and choose:

```text
4. Show my saved command history
```

or open:

```text
website/index.html
```

### 5. Owner dashboard

First set owner email/password in:

```text
backend/.env
```

Then start backend and open admin dashboard:

```text
START_ADMIN_DASHBOARD.bat
```

Open:

```text
http://127.0.0.1:8080
```

## Before Public Deployment

Important: GitHub Pages cannot store login/database data by itself. You need a backend host.

Use one of these:

- Render
- Railway
- VPS
- Supabase/PostgreSQL with FastAPI backend
- Firebase alternative if you rewrite auth

For production:

- Change `FRIDAY_SECRET_KEY`
- Change owner email/password
- Use HTTPS
- Use PostgreSQL instead of local SQLite
- Keep `.env` secret
- Never upload `backend/data/fridayv8.db`
- Never upload passwords or owner key files

## Owner/Author Features

Owner can:

- View dashboard summary
- View users
- View safety events
- Suspend/unsuspend accounts
- Turn maintenance mode on/off
- View owner audit logs

Owner cannot:

- See plain user passwords
- Secretly read personal files
- Secretly read WhatsApp messages
- Secretly read browser history
- Spy on private chats outside FridayV8

## Default local owner

If you do not edit `.env`, the backend creates:

```text
owner@example.com
ChangeThisStrongPassword123!
```

Change this before public use.
