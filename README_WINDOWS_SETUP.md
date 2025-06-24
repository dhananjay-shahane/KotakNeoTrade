
# Kotak Neo Trading App - Windows Local Development Setup

This guide helps you set up and run the Kotak Neo Trading Application on your local Windows machine.

## 🚀 Quick Setup

Run the automated setup script:

```cmd
local_setup_windows.bat
```

This script will automatically:
- Check for Python 3.11 installation
- Check for PostgreSQL installation
- Create a local database
- Install all Python dependencies
- Set up environment variables
- Initialize database tables
- Create utility scripts

## 📋 Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

### 1. Prerequisites

#### Install Python 3.11
1. Download Python 3.11 from [python.org](https://python.org/downloads/windows/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   ```

#### Install PostgreSQL
1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings
3. Remember your postgres user password
4. Add PostgreSQL bin directory to PATH:
   - Default path: `C:\Program Files\PostgreSQL\15\bin`
5. Verify installation:
   ```cmd
   psql --version
   ```

### 2. Database Setup

```cmd
# Create database
createdb -U postgres kotak_neo_local

# Verify connection
psql -U postgres -d kotak_neo_local -c "SELECT version();"
```

### 3. Python Dependencies

```cmd
# Install dependencies
python -m pip install -e .
```

### 4. Environment Configuration

Create a `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/kotak_neo_local

# Session
SESSION_SECRET=your-secret-key-here

# Flask
FLASK_ENV=development
FLASK_DEBUG=True

# Kotak Neo API (Add your credentials)
KOTAK_NEO_CONSUMER_KEY=your_consumer_key
KOTAK_NEO_CONSUMER_SECRET=your_consumer_secret
KOTAK_NEO_ACCESS_TOKEN=your_access_token
KOTAK_NEO_MOBILE_NUMBER=your_mobile_number
KOTAK_NEO_PASSWORD=your_password
```

### 5. Initialize Database

```cmd
python -c "from app import app; from models import db; app.app_context().__enter__(); db.create_all()"
```

## 🏃‍♂️ Running the Application

```cmd
# Start the application
run_local.bat

# Or manually
python main.py
```

Access the application at: `http://localhost:5000`

## 🛠️ Development Tools

### Database Management

```cmd
# Reset database
reset_db.bat

# Backup database
backup_db.bat

# Connect to database
psql -U postgres -d kotak_neo_local
```

### Windows-Specific Commands

```cmd
# Check if PostgreSQL service is running
sc query postgresql-x64-15

# Start PostgreSQL service
net start postgresql-x64-15

# Stop PostgreSQL service
net stop postgresql-x64-15
```

## 📁 Project Structure

```
kotak-neo-trading/
├── api/                    # API endpoints
├── config/                 # Configuration files
├── routes/                 # Route handlers
├── static/                 # Static assets (CSS, JS)
├── templates/              # HTML templates
├── utils/                  # Utility functions
├── .env                    # Environment variables (create this)
├── app.py                  # Main Flask application
├── main.py                 # Application entry point
├── models.py               # Database models
└── local_setup_windows.bat # Windows setup script
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `KOTAK_NEO_CONSUMER_KEY` | Your Kotak Neo API consumer key | Yes |
| `KOTAK_NEO_CONSUMER_SECRET` | Your Kotak Neo API consumer secret | Yes |
| `KOTAK_NEO_ACCESS_TOKEN` | Your Kotak Neo API access token | Yes |
| `KOTAK_NEO_MOBILE_NUMBER` | Your registered mobile number | Yes |
| `KOTAK_NEO_PASSWORD` | Your trading password | Yes |

### Getting Kotak Neo API Credentials

1. Log in to your Kotak Neo account
2. Go to API settings
3. Generate API credentials
4. Update the `.env` file with your credentials

## 🔍 Troubleshooting

### Common Windows Issues

1. **Python not found**
   ```cmd
   # Add Python to PATH manually
   set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
   ```

2. **PostgreSQL not starting**
   ```cmd
   # Start PostgreSQL service
   net start postgresql-x64-15
   
   # Check service status
   sc query postgresql-x64-15
   ```

3. **Permission denied errors**
   ```cmd
   # Run Command Prompt as Administrator
   # Right-click Command Prompt -> "Run as administrator"
   ```

4. **Database connection error**
   ```cmd
   # Check if PostgreSQL is running
   sc query postgresql-x64-15
   
   # Verify database exists
   psql -U postgres -l | findstr kotak_neo_local
   ```

### Path Issues

If you encounter "command not found" errors:

1. **Python Path**: Add Python installation directory to PATH
2. **PostgreSQL Path**: Add `C:\Program Files\PostgreSQL\15\bin` to PATH
3. **Restart Command Prompt** after changing PATH

### Database Issues

```cmd
# Drop and recreate database
dropdb -U postgres kotak_neo_local
createdb -U postgres kotak_neo_local

# Reinitialize tables
python -c "from app import app; from models import db; app.app_context().__enter__(); db.create_all()"
```

## 🚀 Production Deployment

For production deployment, this application is optimized for **Replit**:

1. Push your code to Replit
2. Set environment variables in Replit Secrets
3. The application will auto-deploy with the configured settings

## 📝 Development Workflow

1. Start PostgreSQL service: `net start postgresql-x64-15`
2. Run the application: `run_local.bat`
3. Make your changes
4. Test locally at `http://localhost:5000`
5. Deploy to Replit for production

## 🔒 Security Notes

- Never commit API credentials to version control
- Use strong session secrets
- Keep your `.env` file in `.gitignore`
- Regularly rotate your API keys
- Run antivirus scans regularly on Windows

## 📞 Support

For issues related to:
- **Local setup**: Check this README and troubleshooting section
- **Windows-specific issues**: Check Windows Event Viewer for detailed error logs
- **Kotak Neo API**: Refer to Kotak Neo API documentation
- **Application bugs**: Check the logs and console output

## 🪟 Windows-Specific Notes

- Use Command Prompt (cmd) or PowerShell for running commands
- Ensure Windows Defender doesn't block the application
- Keep Windows and Python up to date
- Consider using Windows Terminal for better command-line experience

---

**Happy Trading on Windows! 📈**
