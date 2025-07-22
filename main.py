
"""
Kotak Neo Trading Platform - Main Application
Enhanced trading platform with real-time data, charts, and signal management
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import secrets

# Add the current directory to Python path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Flask imports
from flask import Flask, session, render_template, redirect, url_for, request, jsonify, flash

# Application imports
from core.database import init_db, db
from routes.main import main_bp
from routes.auth_routes import auth_bp
from api import dashboard, trading_api, deals_api, etf_signals, signals_api, admin_signals_api
from utils.auth import login_required

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load session secret
    session_secret_file = '.session_secret'
    if os.path.exists(session_secret_file):
        try:
            with open(session_secret_file, 'r') as f:
                app.secret_key = f.read().strip()
            logger.info("✓ Loaded session secret from file")
        except Exception as e:
            logger.warning(f"Could not read session secret file: {e}")
            app.secret_key = secrets.token_hex(32)
            logger.info("✓ Generated new session secret")
    else:
        app.secret_key = secrets.token_hex(32)
        logger.warning("Using fallback session secret for development")
    
    # Configure database URI first
    db_uri = os.environ.get('DATABASE_URL')
    if not db_uri:
        db_uri = 'sqlite:///instance/trading_platform.db'
    
    # Configure app settings
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        WTF_CSRF_ENABLED=False  # Disable CSRF for API endpoints
    )
    
    # Initialize database
    try:
        from core.database import db
        db.init_app(app)
        logger.info("✅ Database initialized successfully")
        
        # Create tables
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as table_error:
                logger.error(f"Failed to create tables: {table_error}")
                
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Register blueprints
    try:
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(auth_bp, url_prefix='/trading-account')
        logger.info("✓ Core blueprints registered")
        
        # Register deals blueprint
        try:
            app.register_blueprint(deals_api.deals_bp, url_prefix='/api')
            logger.info("✓ Deals blueprint registered")
        except Exception as deals_error:
            logger.warning(f"Could not register deals blueprint: {deals_error}")
        
        # Register additional API blueprints with error handling
        try:
            if hasattr(dashboard, 'dashboard_bp'):
                app.register_blueprint(dashboard.dashboard_bp, url_prefix='/api')
        except Exception as e:
            logger.warning(f"Could not register dashboard blueprint: {e}")
            
        try:
            if hasattr(trading_api, 'trading_bp'):
                app.register_blueprint(trading_api.trading_bp, url_prefix='/api')
        except Exception as e:
            logger.warning(f"Could not register trading blueprint: {e}")
            
        try:
            if hasattr(etf_signals, 'etf_bp'):
                app.register_blueprint(etf_signals.etf_bp, url_prefix='/api')
        except Exception as e:
            logger.warning(f"Could not register etf_signals blueprint: {e}")
            
        try:
            if hasattr(signals_api, 'signals_bp'):
                app.register_blueprint(signals_api.signals_bp, url_prefix='/api')
        except Exception as e:
            logger.warning(f"Could not register signals blueprint: {e}")
            
        try:
            if hasattr(admin_signals_api, 'admin_bp'):
                app.register_blueprint(admin_signals_api.admin_bp, url_prefix='/api/admin')
        except Exception as e:
            logger.warning(f"Could not register admin signals blueprint: {e}")
        
        logger.info("✓ Blueprints registration completed")
        
    except Exception as e:
        logger.error(f"Blueprint registration error: {e}")
    
    # Initialize additional services
    try:
        from Scripts.auto_sync_triggers import setup_auto_sync_triggers
        setup_auto_sync_triggers()
        logger.info("✓ Auto-sync triggers initialized")
    except Exception as e:
        logger.warning(f"Could not start auto-sync triggers: {e}")
    
    
    
    # Initialize quotes scheduler (optional)
    try:
        from Scripts.realtime_quotes_manager import start_quotes_scheduler
        start_quotes_scheduler()
        logger.info("✓ Quotes scheduler started")
    except Exception as e:
        logger.warning(f"Could not start quotes scheduler: {e}")
    
    # Try to initialize Kotak Neo integration
    try:
        from kotak_neo_project.app import app as kotak_app
        logger.info("✓ Kotak Neo integration available")
    except Exception as e:
        logger.info(f"Kotak Neo integration optional: {e}")
    
    # Initialize email and user management
    try:
        from flask_mail import Mail
        mail = Mail(app)
        
        from Scripts.models import User
        logger.info("✓ Email and login extensions initialized")
        logger.info("✓ User model defined")
        
        # Load email configuration
        app.config.update(
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USERNAME=os.environ.get('EMAIL_USERNAME', ''),
            MAIL_PASSWORD=os.environ.get('EMAIL_PASSWORD', ''),
            MAIL_DEFAULT_SENDER=os.environ.get('EMAIL_USERNAME', 'noreply@kotakneo.com')
        )
        logger.info("✓ Email configuration loaded")
        
    except Exception as e:
        logger.warning(f"Email/User management initialization: {e}")
    
    # Initialize Dash app for charts
    try:
        from dash_charts_app import dash_app
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        
        # Integrate Dash app with Flask
        app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
            '/dash-charts': dash_app.server
        })
        logger.info("✓ Dash charts app integrated")
    except Exception as e:
        logger.warning(f"Could not integrate Dash app: {e}")
    
    # Add global template variables
    @app.context_processor
    def inject_globals():
        return {
            'current_user': session.get('greeting_name', 'User'),
            'is_authenticated': session.get('authenticated', False),
            'app_version': '2.0.0',
            'current_year': datetime.now().year
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            from core.database import db
            db.session.rollback()
        except Exception:
            pass
        return render_template('404.html'), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
    
    return app

# Create the application
app = create_app()

# Request logging middleware
@app.before_request
def log_request_info():
    endpoint = request.endpoint
    if endpoint:
        url = request.url
        logger.info(f"Request to {endpoint}: {url}")

if __name__ == '__main__':
    try:
        logger.info("🚀 Starting Kotak Neo Trading Platform...")
        logger.info("=" * 60)
        logger.info("📊 Platform Features:")
        logger.info("  • Real-time trading dashboard")
        logger.info("  • Interactive candlestick charts")  
        logger.info("  • ETF trading signals")
        logger.info("  • Portfolio management")
        logger.info("  • Automated deal tracking")
        logger.info("=" * 60)
        
        # Run the application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)
