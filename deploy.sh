#!/bin/bash
# Render Deployment Script for Kotak Neo Trading Application

echo "🚀 Starting Kotak Neo Trading deployment on Render..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r render_requirements.txt

# Set up database
echo "🗄️ Setting up database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

# Set environment variables for production
export FLASK_ENV=production
export FLASK_DEBUG=False

echo "✅ Deployment setup complete!"
echo "🌐 Application will be available at your Render domain"