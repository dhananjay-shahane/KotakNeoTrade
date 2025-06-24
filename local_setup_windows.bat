
@echo off
setlocal enabledelayedexpansion

REM Kotak Neo Trading App - Local Setup Script for Windows
REM This script sets up the complete environment for running the trading application locally

echo 🚀 Starting Kotak Neo Trading App Local Setup for Windows...

REM Colors for output (Windows CMD doesn't support colors well, but we'll use echo for status)
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

echo.
echo 📋 Kotak Neo Trading Application Setup for Windows
echo.

REM Step 1: Check for Python 3.11
echo 🐍 Step 1: Checking Python 3.11 installation...
python --version 2>nul | findstr "3.11" >nul
if errorlevel 1 (
    echo ⚠️  Python 3.11 not found. Please install Python 3.11 from https://python.org
    echo    Make sure to check "Add Python to PATH" during installation
    echo.
    echo    After installing Python, re-run this script.
    pause
    exit /b 1
) else (
    echo ✅ Python 3.11 is installed
)

REM Step 2: Check for PostgreSQL
echo.
echo 🗄️  Step 2: Checking PostgreSQL installation...
where psql >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PostgreSQL not found. Please install PostgreSQL from https://postgresql.org/download/windows/
    echo    After installation, make sure to add PostgreSQL bin directory to your PATH
    echo    Default path: C:\Program Files\PostgreSQL\15\bin
    echo.
    echo    After installing PostgreSQL, re-run this script.
    pause
    exit /b 1
) else (
    echo ✅ PostgreSQL is installed
)

REM Step 3: Create database
echo.
echo 💾 Step 3: Setting up database...
set DB_NAME=kotak_neo_local
set DB_USER=%USERNAME%

REM Check if database exists
psql -U %USERNAME% -lqt 2>nul | findstr "%DB_NAME%" >nul
if errorlevel 1 (
    echo ⚠️  Creating database '%DB_NAME%'...
    createdb -U %USERNAME% %DB_NAME%
    if errorlevel 1 (
        echo ❌ Failed to create database. Please ensure PostgreSQL is properly configured.
        echo    You may need to set up a postgres user or configure authentication.
        pause
        exit /b 1
    )
    echo ✅ Database '%DB_NAME%' created successfully
) else (
    echo ✅ Database '%DB_NAME%' already exists
)

REM Step 4: Install pip if not available
echo.
echo 📦 Step 4: Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pip not found. Installing pip...
    python -m ensurepip --upgrade
) else (
    echo ✅ pip is available
)

REM Step 5: Install Python dependencies
echo.
echo 📚 Step 5: Installing Python dependencies...
echo Installing dependencies from pyproject.toml...
python -m pip install -e .
if errorlevel 1 (
    echo ❌ Failed to install dependencies. Check your internet connection and try again.
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Step 6: Set up environment variables
echo.
echo 🔧 Step 6: Setting up environment variables...
set ENV_FILE=.env

if not exist "%ENV_FILE%" (
    echo ⚠️  Creating .env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://%DB_USER%@localhost:5432/%DB_NAME%
        echo.
        echo # Session Configuration
        echo SESSION_SECRET=your-generated-secret-key-here
        echo.
        echo # Flask Configuration
        echo FLASK_ENV=development
        echo FLASK_DEBUG=True
        echo.
        echo # Trading Configuration ^(Add your actual values^)
        echo # KOTAK_NEO_CONSUMER_KEY=your_consumer_key_here
        echo # KOTAK_NEO_CONSUMER_SECRET=your_consumer_secret_here
        echo # KOTAK_NEO_ACCESS_TOKEN=your_access_token_here
        echo # KOTAK_NEO_MOBILE_NUMBER=your_mobile_number_here
        echo # KOTAK_NEO_PASSWORD=your_password_here
        echo.
        echo # Optional: Logging level
        echo LOG_LEVEL=DEBUG
    ) > "%ENV_FILE%"
    echo ✅ .env file created with basic configuration
    echo ⚠️  Please update the Kotak Neo API credentials in .env file
) else (
    echo ✅ .env file already exists
)

REM Step 7: Initialize database tables
echo.
echo 🏗️  Step 7: Initializing database tables...
echo Creating database tables...
python -c "import os; os.environ['DATABASE_URL'] = 'postgresql://%DB_USER%@localhost:5432/%DB_NAME%'; from app import app; from models import db; app.app_context().__enter__(); db.create_all(); print('✅ Database tables created successfully')"
if errorlevel 1 (
    echo ❌ Failed to create database tables. Check your database connection.
    pause
    exit /b 1
)

REM Step 8: Create run script
echo.
echo 🏃 Step 8: Creating run script...
(
    echo @echo off
    echo.
    echo REM Load environment variables from .env file
    echo if exist .env ^(
    echo     for /f "usebackq tokens=1,2 delims==" %%%%a in ^(".env"^) do ^(
    echo         if not "%%%%a"=="" if not "%%%%a:~0,1%"=="#" set "%%%%a=%%%%b"
    echo     ^)
    echo ^)
    echo.
    echo REM Start the Flask application
    echo echo 🚀 Starting Kotak Neo Trading Application...
    echo echo 📊 Dashboard will be available at: http://localhost:5000
    echo echo 🔒 Make sure to configure your Kotak Neo API credentials in .env file
    echo echo.
    echo.
    echo python main.py
) > run_local.bat
echo ✅ Run script created: run_local.bat

REM Step 9: Create development utilities
echo.
echo 🛠️  Step 9: Creating development utilities...

REM Database reset script
(
    echo @echo off
    echo echo 🔄 Resetting database...
    echo dropdb -U %DB_USER% %DB_NAME% 2>nul
    echo createdb -U %DB_USER% %DB_NAME%
    echo python -c "import os; os.environ['DATABASE_URL'] = 'postgresql://%DB_USER%@localhost:5432/%DB_NAME%'; from app import app; from models import db; app.app_context().__enter__(); db.create_all(); print('✅ Database reset complete')"
) > reset_db.bat

REM Backup script
(
    echo @echo off
    echo set BACKUP_FILE=backup_%%date:~-4,4%%%%date:~-10,2%%%%date:~-7,2%%_%%time:~0,2%%%%time:~3,2%%%%time:~6,2%%.sql
    echo set BACKUP_FILE=!BACKUP_FILE: =0!
    echo echo 💾 Creating database backup: %%BACKUP_FILE%%
    echo pg_dump -U %DB_USER% %DB_NAME% > %%BACKUP_FILE%%
    echo echo ✅ Backup created: %%BACKUP_FILE%%
) > backup_db.bat

echo ✅ Development utilities created

REM Final instructions
echo.
echo 🎉 Setup Complete!
echo.
echo 📋 Next Steps:
echo 1. Update your Kotak Neo API credentials in the .env file:
echo    - KOTAK_NEO_CONSUMER_KEY
echo    - KOTAK_NEO_CONSUMER_SECRET
echo    - KOTAK_NEO_ACCESS_TOKEN
echo    - KOTAK_NEO_MOBILE_NUMBER
echo    - KOTAK_NEO_PASSWORD
echo.
echo 2. Run the application:
echo    ✅ run_local.bat
echo.
echo 3. Access the dashboard at:
echo    ✅ http://localhost:5000
echo.
echo 🛠️  Available Scripts:
echo    ✅ run_local.bat     - Start the application
echo    ✅ reset_db.bat      - Reset the database
echo    ✅ backup_db.bat     - Backup the database
echo.
echo ⚠️  Important Notes:
echo    - Make sure PostgreSQL service is running
echo    - For production deployment, use Replit (already configured)
echo    - Keep your API credentials secure and never commit them to version control
echo.
echo ✨ Happy Trading!
echo.
pause
