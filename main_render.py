"""
Render-optimized entry point for Kotak Neo Trading Application
This file ensures proper startup for Render deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup library paths for pandas/numpy dependencies
def setup_library_paths():
    """Setup LD_LIBRARY_PATH for required libraries"""
    # For Render, we don't need to set custom library paths
    pass

# Setup environment
setup_library_paths()

# Import the main Flask app
from app import app

# Ensure proper configuration for production
if os.environ.get('ENVIRONMENT') == 'production':
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

# Set up database tables for production
with app.app_context():
    from app import db
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database setup error: {e}")
    
# For Render deployment, we need to ensure the app is available as 'application'
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)