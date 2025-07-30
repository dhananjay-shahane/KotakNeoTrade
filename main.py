"""
Main entry point for the Kotak Neo Trading Platform
Handles environment setup, library paths, and blueprint registration
"""
import os
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

def setup_library_paths():
    """
    Configure library paths for pandas/numpy dependencies
    Required for Replit environment compatibility
    """
    library_path = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    os.environ['LD_LIBRARY_PATH'] = library_path
    print(f"Set LD_LIBRARY_PATH: {library_path}")

# Setup environment before importing Flask modules
setup_library_paths()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import main Flask application
from app import app

# Import additional API blueprints
from api.default_deals_api import default_deals_api
from api.password_reset_api import password_reset_bp

if __name__ == '__main__':
    try:
        print("🚀 Starting Kotak Neo Trading Platform...")
        # Configure server settings
        port = int(os.environ.get('PORT', 5000))

        print(f"🌐 Server starting on:")
        print(f"   Local: http://0.0.0.0:{port}")
        if os.environ.get('REPLIT_DOMAINS'):
            print(f"   External: https://{os.environ.get('REPLIT_DOMAINS')}")

        # Register blueprints
        app.register_blueprint(default_deals_api)
        print("✓ Registered default_deals_api blueprint")

        app.register_blueprint(password_reset_bp)

        # Start Flask application server
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)

    except Exception as e:
        print(f"❌ Application startup failed: {str(e)}")
        import traceback
        traceback.print_exc()