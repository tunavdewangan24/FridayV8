# FridayV8 Secure Login Database - Step-by-Step Guide

## What this version adds

This package adds login and database features to FridayV8:

- User register/login by email
- Password hashing
- Command history saved under user email
- User can check history later
- Owner/Author dashboard
- Suspend/unsuspend users
- Maintenance mode
- Safety logs
- Audit logs

## Important note about website publishing

A normal GitHub Pages website cannot run a database/login backend. GitHub Pages only hosts static HTML/CSS/JS.

So the correct setup is:

```text
GitHub Pages = public website
GitHub Releases = app download
Backend host = login + database API
Database = user data storage
```

For local testing, this package uses:

```text
FastAPI backend + SQLite database
```

For public release, use:

```text
FastAPI backend + PostgreSQL database + HTTPS hosting
```

## Local test steps

### Step 1: Start backend

Double-click:

```text
RUN_BACKEND.bat
```

Wait until you see:

```text
Uvicorn running on http://127.0.0.1:8000
```

Do not close this window while testing.

### Step 2: Create your user account

Double-click:

```text
LOGIN_SETUP.bat
```

Choose:

```text
1. Register new account
```

Enter your name, email, and password.

### Step 3: Start FridayV8

Double-click:

```text
START_TEXT_MODE.bat
```

Type a command like:

```text
open chrome and search python tutorial on youtube
```

That command will be saved in the database under your email.

### Step 4: Check your history

Open:

```text
LOGIN_SETUP.bat
```

Choose:

```text
4. Show my saved command history
```

### Step 5: Owner dashboard

Before public use, edit:

```text
backend/.env
```

Change:

```text
FRIDAY_OWNER_EMAIL
FRIDAY_OWNER_PASSWORD
FRIDAY_SECRET_KEY
```

Then run:

```text
RUN_BACKEND.bat
START_ADMIN_DASHBOARD.bat
```

Open:

```text
http://127.0.0.1:8080
```

Login with owner email/password.

## Publish steps

### Step 1: Create GitHub repository

Name it:

```text
FridayV8
```

### Step 2: Upload files

Upload all files/folders from this package except:

```text
backend/data/fridayv8.db
.env
*.log
*.fridaykey
```

### Step 3: Build EXE with GitHub Actions

Open:

```text
Actions → Build FridayV8 Windows EXE → Run workflow
```

Download artifact:

```text
FridayV8-Windows-EXE
```

### Step 4: Create GitHub Release

Tag:

```text
v1.0.0
```

Title:

```text
FridayV8 v1.0.0
```

Upload:

```text
FridayV8.exe
```

### Step 5: Website

You can upload the `/website` folder to GitHub Pages.

But remember: for login/history to work publicly, the backend must also be deployed.

## Production backend checklist

Before giving it to public users:

- Use a real backend host
- Use HTTPS
- Use PostgreSQL
- Change secret key
- Change owner email/password
- Keep `.env` private
- Add proper privacy policy
- Add terms of use
- Test with 2-3 users first

## Safe owner system

Owner can manage app safety and users, but the system is not built for hidden spying.

Allowed owner actions:

- View users
- Suspend user
- Unsuspend user
- View safety events
- Enable maintenance mode
- View audit logs

Not allowed:

- Read plain passwords
- Steal user files
- Read WhatsApp messages
- Read browser history
- Secret screen recording
