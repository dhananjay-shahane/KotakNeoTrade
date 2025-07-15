"""
Kotak Neo Trading Platform - Clean and Optimized Main Flask Application
Modular architecture with separated concerns for better maintainability
"""

# ========================================
# CORE IMPORTS AND ENVIRONMENT SETUP
# ========================================

import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

# Flask core imports
from flask import Flask, request, make_response
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

# Database imports
from core.database import db, init_db

# Load environment variables
load_dotenv()


def setup_library_paths():
    """Configure library paths for Replit environment compatibility"""
    library_path = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    os.environ['LD_LIBRARY_PATH'] = library_path
    print(f"Set LD_LIBRARY_PATH: {library_path}")

    # Preload essential libraries for stability
    try:
        import ctypes
        import ctypes.util
        libstdc = ctypes.util.find_library('stdc++')
        if libstdc:
            ctypes.CDLL(libstdc)
            print("Preloaded libstdc++")
    except Exception as e:
        print(f"Library preload warning: {e}")


# Setup environment before importing Flask modules
setup_library_paths()


# Database is imported from core.database module


# ========================================
# FLASK APPLICATION FACTORY
# ========================================

def create_app():
    """Create and configure Flask application with modular architecture"""
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # ========================================
    # APPLICATION CONFIGURATION
    # ========================================
    
    # Security configuration with fallback
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        session_secret = "replit-kotak-neo-trading-platform-secret-key-2025"
        print("Using fallback session secret for development")
    app.secret_key = session_secret
    
    # Proxy configuration for HTTPS URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration with fallback
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "sqlite:///trading_platform.db"
        print("Using SQLite fallback database for development")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Replit deployment configuration
    app.config['APPLICATION_ROOT'] = '/'
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SERVER_NAME'] = None
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Force HTTPS for external access
    if os.environ.get('REPLIT_DOMAINS'):
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Session configuration for webview compatibility
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = None
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    
    # Flask session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_FILE_DIR'] = './flask_session'
    app.config['SESSION_FILE_THRESHOLD'] = 500
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # ========================================
    # DATABASE INITIALIZATION
    # ========================================
    
    # Initialize database with app using centralized function
    init_db(app)
    
    # Initialize Flask session
    Session(app)
    
    # ========================================
    # MIDDLEWARE AND ERROR HANDLERS
    # ========================================
    
    @app.after_request
    def after_request(response):
        """Configure response headers for webview compatibility"""
        # Remove headers that could interfere with webview display
        headers_to_remove = [
            'X-Frame-Options', 'frame-options', 'Content-Security-Policy',
            'X-XSS-Protection', 'Referrer-Policy', 'Permissions-Policy',
            'X-Content-Type-Options', 'Strict-Transport-Security'
        ]
        for header in headers_to_remove:
            response.headers.pop(header, None)
        
        # Complete webview compatibility
        response.headers.pop('X-Frame-Options', None)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Minimal caching headers
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Pragma'] = 'no-cache'
        
        return response
    
    @app.errorhandler(404)
    def page_not_found(error):
        """Custom 404 error page with authentication check"""
        from core.auth import validate_current_session
        from flask import flash, redirect, url_for, render_template
        
        if not validate_current_session():
            flash('Please login to access this application', 'error')
            return redirect(url_for('auth_routes.login'))
        
        return render_template('404.html'), 404
    
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests"""
        if request.endpoint:
            print(f"Request to {request.endpoint}: {request.url}")
        
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response
    
    # ========================================
    # BLUEPRINT REGISTRATION
    # ========================================
    
    def register_blueprints():
        """Register all application blueprints"""
        try:
            # Main routes
            from routes.main_routes import main_bp
            from routes.auth_routes import auth_bp
            
            # API routes
            from api.dashboard_api import dashboard_bp
            from api.trading_api import trading_bp
            from api.signals_api import signals_bp
            
            # Register blueprints
            app.register_blueprint(main_bp)
            app.register_blueprint(auth_bp)
            app.register_blueprint(dashboard_bp)
            app.register_blueprint(trading_bp)
            app.register_blueprint(signals_bp)
            
            print("✓ All blueprints registered successfully")
            
        except Exception as e:
            logging.error(f"Error registering blueprints: {e}")
            print(f"✗ Blueprint registration failed: {e}")
    
    # Register all blueprints
    register_blueprints()
    
    # ========================================
    # BACKGROUND SERVICES INITIALIZATION
    # ========================================
    
    def start_background_services():
        """Start background schedulers and services"""
        try:
            # Start admin signals scheduler if available
            try:
                from Scripts.admin_signals_scheduler import start_admin_signals_scheduler
                start_admin_signals_scheduler()
                print("✓ Admin signals scheduler started")
            except Exception as e:
                print(f"Warning: Could not start admin signals scheduler: {e}")
            
            # Start real-time quotes manager if available
            try:
                from Scripts.realtime_quotes_manager import start_quotes_scheduler
                start_quotes_scheduler()
                print("✓ Real-time quotes scheduler started")
            except Exception as e:
                print(f"Warning: Could not start quotes scheduler: {e}")
                
        except Exception as e:
            logging.error(f"Error starting background services: {e}")
    
    # Start background services
    start_background_services()
    
    # ========================================
    # LOGGING CONFIGURATION
    # ========================================
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logging.info("✅ Kotak Neo Trading Platform initialized successfully")
    logging.info("✅ Using modular architecture with separated concerns")
    
    return app


# ========================================
# APPLICATION INSTANCE
# ========================================

# Create the Flask application
app = create_app()

# Export for compatibility
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)