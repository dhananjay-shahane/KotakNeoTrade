
#!/bin/bash

# Kotak Neo Trading App - Local Setup Script for macOS
# This script sets up the complete environment for running the trading application locally

set -e  # Exit on any error

echo "🚀 Starting Kotak Neo Trading App Local Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS. For other systems, please refer to the documentation."
    exit 1
fi

print_info "Setting up Kotak Neo Trading Application on macOS..."

# Step 1: Check and install Homebrew
echo -e "\n${BLUE}📦 Step 1: Installing Homebrew (if not installed)...${NC}"
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    print_status "Homebrew is already installed"
fi

# Step 2: Install Python 3.11
echo -e "\n${BLUE}🐍 Step 2: Installing Python 3.11...${NC}"
if ! python3.11 --version &> /dev/null; then
    print_warning "Python 3.11 not found. Installing..."
    brew install python@3.11
else
    print_status "Python 3.11 is already installed"
fi

# Step 3: Install PostgreSQL
echo -e "\n${BLUE}🗄️  Step 3: Installing PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL not found. Installing..."
    brew install postgresql@15
    brew services start postgresql@15
    
    # Add PostgreSQL to PATH
    echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
else
    print_status "PostgreSQL is already installed"
    # Ensure PostgreSQL is running
    brew services start postgresql@15 2>/dev/null || true
fi

# Step 4: Create database
echo -e "\n${BLUE}💾 Step 4: Setting up database...${NC}"
DB_NAME="kotak_neo_local"
DB_USER=$(whoami)

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    print_status "Database '$DB_NAME' already exists"
else
    print_warning "Creating database '$DB_NAME'..."
    createdb $DB_NAME
    print_status "Database '$DB_NAME' created successfully"
fi

# Step 5: Install uv (Python package manager)
echo -e "\n${BLUE}📦 Step 5: Installing uv package manager...${NC}"
if ! command -v uv &> /dev/null; then
    print_warning "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
else
    print_status "uv is already installed"
fi

# Step 6: Install Python dependencies
echo -e "\n${BLUE}📚 Step 6: Installing Python dependencies...${NC}"
print_info "Installing dependencies from pyproject.toml..."
uv pip install -e .

# Step 7: Set up environment variables
echo -e "\n${BLUE}🔧 Step 7: Setting up environment variables...${NC}"
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    print_warning "Creating .env file..."
    cat > $ENV_FILE << EOF
# Database Configuration
DATABASE_URL=postgresql://$DB_USER@localhost:5432/$DB_NAME

# Session Configuration
SESSION_SECRET=$(openssl rand -hex 32)

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Trading Configuration (Add your actual values)
# KOTAK_NEO_CONSUMER_KEY=your_consumer_key_here
# KOTAK_NEO_CONSUMER_SECRET=your_consumer_secret_here
# KOTAK_NEO_ACCESS_TOKEN=your_access_token_here
# KOTAK_NEO_MOBILE_NUMBER=your_mobile_number_here
# KOTAK_NEO_PASSWORD=your_password_here

# Optional: Logging level
LOG_LEVEL=DEBUG
EOF
    print_status ".env file created with basic configuration"
    print_warning "Please update the Kotak Neo API credentials in .env file"
else
    print_status ".env file already exists"
fi

# Step 8: Initialize database tables
echo -e "\n${BLUE}🏗️  Step 8: Initializing database tables...${NC}"
print_info "Creating database tables..."
python3.11 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://$DB_USER@localhost:5432/$DB_NAME'
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('✅ Database tables created successfully')
"

# Step 9: Create run script
echo -e "\n${BLUE}🏃 Step 9: Creating run script...${NC}"
cat > run_local.sh << 'EOF'
#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the Flask application
echo "🚀 Starting Kotak Neo Trading Application..."
echo "📊 Dashboard will be available at: http://localhost:5000"
echo "🔒 Make sure to configure your Kotak Neo API credentials in .env file"
echo ""

python3.11 main.py
EOF

chmod +x run_local.sh
print_status "Run script created: ./run_local.sh"

# Step 10: Create development utilities
echo -e "\n${BLUE}🛠️  Step 10: Creating development utilities...${NC}"

# Database reset script
cat > reset_db.sh << EOF
#!/bin/bash
echo "🔄 Resetting database..."
dropdb $DB_NAME 2>/dev/null || true
createdb $DB_NAME
python3.11 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://$DB_USER@localhost:5432/$DB_NAME'
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('✅ Database reset complete')
"
EOF
chmod +x reset_db.sh

# Backup script
cat > backup_db.sh << EOF
#!/bin/bash
BACKUP_FILE="backup_\$(date +%Y%m%d_%H%M%S).sql"
echo "💾 Creating database backup: \$BACKUP_FILE"
pg_dump $DB_NAME > \$BACKUP_FILE
echo "✅ Backup created: \$BACKUP_FILE"
EOF
chmod +x backup_db.sh

print_status "Development utilities created"

# Final instructions
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo "1. Update your Kotak Neo API credentials in the .env file:"
echo "   - KOTAK_NEO_CONSUMER_KEY"
echo "   - KOTAK_NEO_CONSUMER_SECRET" 
echo "   - KOTAK_NEO_ACCESS_TOKEN"
echo "   - KOTAK_NEO_MOBILE_NUMBER"
echo "   - KOTAK_NEO_PASSWORD"
echo ""
echo "2. Run the application:"
echo "   ${GREEN}./run_local.sh${NC}"
echo ""
echo "3. Access the dashboard at:"
echo "   ${GREEN}http://localhost:5000${NC}"
echo ""
echo -e "${BLUE}🛠️  Available Scripts:${NC}"
echo "   ${GREEN}./run_local.sh${NC}     - Start the application"
echo "   ${GREEN}./reset_db.sh${NC}      - Reset the database"
echo "   ${GREEN}./backup_db.sh${NC}     - Backup the database"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "   - Make sure PostgreSQL is running: brew services start postgresql@15"
echo "   - For production deployment, use Replit (already configured)"
echo "   - Keep your API credentials secure and never commit them to version control"
echo ""
echo -e "${GREEN}✨ Happy Trading!${NC}"
