# Employee Management System

A Flask and MySQL application for managing employee records, salaries, attendance, leave balances, and account credentials.

## What is included

- Employee self-registration and secure login
- Administrator-only employee, salary, attendance, and leave management
- Per-user sessions and role-based access control
- Hashed passwords with automatic upgrading of legacy plain-text records after login
- CSRF protection, secure session cookies, and security response headers
- Parameterized database queries and validated numeric inputs
- Environment-based configuration; no database password or fixed Flask secret in source code

## Technology

- **Frontend:** HTML, Bootstrap, JavaScript
- **Backend:** Python 3, Flask
- **Database:** MySQL 8+

## Setup on Windows 10 / PowerShell

### 1. Install prerequisites

Install Python 3.11+, MySQL 8+, and ensure both `python` and `mysql` are available in PowerShell.

### 2. Create a virtual environment and install dependencies

```powershell
git clone https://github.com/Shadow-Taslim/Employee-Management-System.git
cd Employee-Management-System
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure the application

```powershell
Copy-Item .env.example .env
notepad .env
```

Set a unique `SECRET_KEY`, your MySQL credentials, and the database name. The `.env` file is ignored by Git. You can generate a suitable secret with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Create and populate the database

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS employee_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cmd /c "mysql -u root -p employee_management < server\First.sql"
```

The SQL file contains demonstration employee data. Existing databases can continue to be used; plain-text passwords are upgraded automatically when their owners successfully log in.

### 5. Create an administrator

Choose an existing employee ID from the `official` table, then run:

```powershell
flask --app server.app2 create-admin 101
```

The command prompts for a username and password. Public registration only creates employee accounts; signed-in administrators can create additional administrator accounts.

### 6. Run the application

```powershell
python server/app2.py
```

Open `http://127.0.0.1:5000`. Debug mode is disabled unless `FLASK_DEBUG=1` is explicitly set in `.env`.

## Run tests

The tests use mocked database access and do not require a running MySQL server.

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
client/                  HTML templates and static assets
server/app2.py           Flask routes, authentication, and database access
server/First.sql         MySQL schema and demonstration data
tests/test_app.py        Authentication and authorization tests
.env.example             Documented configuration template
runtime-requirements.txt Python runtime dependencies
```

## Deployment notes

Use HTTPS and set `SESSION_COOKIE_SECURE=true` in production. Run the app with a production WSGI server rather than Flask's development server, keep `.env` private, and replace the demonstration data before real use.
