
@echo off
setlocal enabledelayedexpansion

REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" set "%%a=%%b"
    )
)

REM Start the Flask application
echo.
echo 🚀 Starting Kotak Neo Trading Application...
echo 📊 Dashboard will be available at: http://localhost:5000
echo 🔒 Make sure to configure your Kotak Neo API credentials in .env file
echo.
echo Press Ctrl+C to stop the application
echo.

python main.py

echo.
echo Application stopped.
pause
