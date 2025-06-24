# Local Development Setup Guide

## The Problem
Your error shows: `could not translate host name "123@localhost"` - this means your local .env file has an incorrect database URL format.

## Solution Steps

### 1. Install PostgreSQL on Windows
Download and install PostgreSQL from: https://www.postgresql.org/download/windows/
- During installation, remember the password you set for the 'postgres' user
- Default port is usually 5432

### 2. Create Local Database
Open Command Prompt or PowerShell as Administrator:
```cmd
# Connect to PostgreSQL
psql -U postgres

# Create database for your project
CREATE DATABASE kotak_trading_db;

# Create a user (optional but recommended)
CREATE USER kotak_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE kotak_trading_db TO kotak_user;

# Exit PostgreSQL
\q
```

### 3. Update Your Local .env File
Create or update your `.env` file in your project root:

```env
# Local PostgreSQL Database
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/kotak_trading_db

# OR if you created a specific user:
# DATABASE_URL=postgresql://kotak_user:your_password_here@localhost:5432/kotak_trading_db

# Session Secret
SESSION_SECRET=your-local-secret-key-change-this

# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True

# Kotak Neo API (add your credentials)
KOTAK_CONSUMER_KEY=
KOTAK_CONSUMER_SECRET=
KOTAK_ACCESS_TOKEN=
KOTAK_ACCESS_TOKEN_SECRET=
```

### 4. Install Python Dependencies
```cmd
# Make sure you're in your project directory
cd C:\01_KotakNeoTrader-main\KotakNeoTrader-main

# Activate virtual environment
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# OR install manually if no requirements.txt:
pip install flask flask-sqlalchemy psycopg2-binary python-dotenv flask-session pandas neo-api-client gunicorn email-validator werkzeug
```

### 5. Test the Setup
```cmd
python main.py
```

## Alternative: Using SQLite for Local Development
If PostgreSQL setup is too complex, you can use SQLite locally:

Update your local `.env`:
```env
# SQLite Database (simpler for local development)
DATABASE_URL=sqlite:///kotak_trading.db

SESSION_SECRET=your-local-secret-key-change-this
FLASK_ENV=development
FLASK_DEBUG=True
```

Then run:
```cmd
python main.py
```

## Common Issues and Solutions

### Issue 1: psycopg2 installation fails
```cmd
pip install psycopg2-binary
# instead of just psycopg2
```

### Issue 2: Port already in use
Change the port in your run command:
```cmd
flask run --port=5001
```

### Issue 3: Database connection still fails
Check if PostgreSQL service is running:
- Windows: Services → PostgreSQL should be "Running"
- Or restart it: `net start postgresql-x64-13` (adjust version number)

## Verification Steps
1. Database connects without errors
2. Web application starts on http://localhost:5000
3. Login page loads properly
4. No console errors in browser developer tools

## Need Help?
If you're still having issues, check:
1. PostgreSQL is installed and running
2. Database name and credentials are correct in .env
3. All Python packages are installed
4. Firewall isn't blocking the connection