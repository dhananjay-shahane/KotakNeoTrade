
# Kotak Neo Trading App - Local Development Setup

This guide helps you set up and run the Kotak Neo Trading Application on your local macOS machine.

## 🚀 Quick Setup

Run the automated setup script:

```bash
chmod +x local_setup.sh
./local_setup.sh
```

This script will automatically:
- Install Homebrew (if not present)
- Install Python 3.11
- Install PostgreSQL
- Create a local database
- Install all Python dependencies
- Set up environment variables
- Initialize database tables
- Create utility scripts

## 📋 Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

### 1. Prerequisites

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install PostgreSQL
brew install postgresql@15
brew services start postgresql@15
```

### 2. Database Setup

```bash
# Create database
createdb kotak_neo_local

# Verify connection
psql kotak_neo_local -c "SELECT version();"
```

### 3. Python Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

### 4. Environment Configuration

Create a `.env` file with your configuration:

```bash
# Database
DATABASE_URL=postgresql://$(whoami)@localhost:5432/kotak_neo_local

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

```bash
python3.11 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
"
```

## 🏃‍♂️ Running the Application

```bash
# Start the application
./run_local.sh

# Or manually
python3.11 main.py
```

Access the application at: `http://localhost:5000`

## 🛠️ Development Tools

### Database Management

```bash
# Reset database
./reset_db.sh

# Backup database
./backup_db.sh

# Connect to database
psql kotak_neo_local
```

### Logs and Debugging

```bash
# View application logs
tail -f logs/app.log

# Debug mode (already enabled in .env)
export FLASK_DEBUG=True
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
└── requirements files      # Dependencies
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

### Common Issues

1. **PostgreSQL not starting**
   ```bash
   brew services restart postgresql@15
   ```

2. **Python module not found**
   ```bash
   uv pip install -e .
   ```

3. **Database connection error**
   ```bash
   # Check if PostgreSQL is running
   brew services list | grep postgresql
   
   # Verify database exists
   psql -l | grep kotak_neo_local
   ```

4. **Permission denied errors**
   ```bash
   chmod +x local_setup.sh
   chmod +x run_local.sh
   ```

### Database Issues

```bash
# Drop and recreate database
dropdb kotak_neo_local
createdb kotak_neo_local

# Reinitialize tables
python3.11 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
"
```

## 🚀 Production Deployment

For production deployment, this application is optimized for **Replit**:

1. Push your code to Replit
2. Set environment variables in Replit Secrets
3. The application will auto-deploy with the configured settings

## 📝 Development Workflow

1. Start PostgreSQL: `brew services start postgresql@15`
2. Run the application: `./run_local.sh`
3. Make your changes
4. Test locally at `http://localhost:5000`
5. Deploy to Replit for production

## 🔒 Security Notes

- Never commit API credentials to version control
- Use strong session secrets
- Keep your `.env` file in `.gitignore`
- Regularly rotate your API keys

## 📞 Support

For issues related to:
- **Local setup**: Check this README and troubleshooting section
- **Kotak Neo API**: Refer to Kotak Neo API documentation
- **Application bugs**: Check the logs and console output

---

**Happy Trading! 📈**
