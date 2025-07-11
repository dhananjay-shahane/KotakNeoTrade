"""
Kotak Neo Trading Platform - Main Flask Application
Provides a comprehensive trading interface with real-time market data,
portfolio management, and automated trading signals.
"""

# ========================================
# ALL IMPORTS - ORGANIZED AT TOP
# ========================================

# Standard library imports
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from functools import wraps

# Third-party imports
from dotenv import load_dotenv
from flask import Flask, request, make_response, redirect, url_for, render_template, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Functions imports
from functions.positions.positions import positions
from functions.holdings.holdings import holdings
from functions.orders.orders import orders
from functions.dashboard.dashboard import dashboard
from functions.dashboard.dashboard_data import get_dashboard_data_api

# Load environment variables from .env file
load_dotenv()


def setup_library_paths():
    """
    Configure library paths for pandas/numpy dependencies
    Required for Replit environment compatibility with scientific libraries
    """
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

# ========================================
# FLASK APPLICATION SETUP
# ========================================

# Flask imports already added to top section


class Base(DeclarativeBase):
    """Base class for SQLAlchemy database models"""
    pass


# Initialize Flask application and database
db = SQLAlchemy(model_class=Base)
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
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1,
                        x_host=1)  # Enable HTTPS URL generation

# Database configuration with fallback
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback to SQLite for development
    database_url = "sqlite:///trading_platform.db"
    print("Using SQLite fallback database for development")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,  # Recycle connections every 5 minutes
    "pool_pre_ping": True,  # Verify connections before use
}

# Configure Flask for Replit deployment and external access
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SERVER_NAME'] = None
# Webview compatibility
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Force HTTPS for external access
if os.environ.get('REPLIT_DOMAINS'):
    app.config['PREFERRED_URL_SCHEME'] = 'https'

# Allow all origins for external access
app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Session configuration for webview compatibility
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'


# Configure for Replit webview and DNS
@app.after_request
def after_request(response):
    # Remove ALL headers that could interfere with webview display
    headers_to_remove = [
        'X-Frame-Options', 'frame-options', 'Content-Security-Policy',
        'X-XSS-Protection', 'Referrer-Policy', 'Permissions-Policy',
        'X-Content-Type-Options', 'Strict-Transport-Security'
    ]
    for header in headers_to_remove:
        response.headers.pop(header, None)

    # Complete webview compatibility - remove X-Frame-Options entirely
    response.headers.pop('X-Frame-Options', None)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    # Minimal caching headers
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Pragma'] = 'no-cache'

    return response


# Handle preflight requests and ensure proper routing
@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page with authentication check"""
    # Check if user is authenticated before showing 404 page
    if not validate_current_session():
        flash('Please login to access this application', 'error')
        return redirect(url_for('login'))

    return render_template('404.html'), 404


@app.before_request
def handle_preflight():
    # Log request for debugging
    if request.endpoint:
        print(f"Request to {request.endpoint}: {request.url}")

    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


# Import Flask components
from flask import render_template, request, redirect, url_for, session, jsonify, flash, make_response

# Root route - ultra-simple webview
# @app.route('/')
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import Scripts.models as models  # noqa: F401
    import Scripts.models_etf as models_etf  # noqa: F401

    db.create_all()

# Import and add routes
from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
import logging
import json
from datetime import datetime, timedelta

# Configure session for persistent storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
Session(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize helper classes
from Scripts.neo_client import NeoClient
from Scripts.trading_functions import TradingFunctions
from Scripts.user_manager import UserManager
from Scripts.session_helper import SessionHelper
from Scripts.websocket_handler import WebSocketHandler
# Supabase integration removed
supabase_client = None

neo_client = NeoClient()
trading_functions = TradingFunctions()
user_manager = UserManager()
session_helper = SessionHelper()
websocket_handler = WebSocketHandler()

# Supabase integration removed
logging.info("✅ Using local PostgreSQL database only")


def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Real-time mode - use actual Kotak Neo API authentication
        demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
        if demo_mode:
            if not session.get('authenticated'):
                session['authenticated'] = True
                session['ucc'] = 'DEMO001'
                session['greeting_name'] = 'Demo User'
                session['access_token'] = 'demo_token'
                session['session_token'] = 'demo_session'
                session['client'] = 'demo_client'
                session.permanent = True
            return True

        # Check if user is authenticated
        if not session.get('authenticated'):
            return False

        # Check session expiration
        session_expires_at = session.get('session_expires_at')
        if session_expires_at:
            from datetime import datetime
            if datetime.now() > datetime.fromisoformat(session_expires_at):
                session.clear()
                return False

        # Check if required session data exists
        required_fields = ['access_token', 'session_token', 'ucc']
        for field in required_fields:
            if not session.get(field):
                logging.warning(f"Missing session field: {field}")
                session.clear()
                return False

        return True

    except Exception as e:
        logging.error(f"Session validation error: {e}")
        session.clear()
        return False


def require_auth(f):
    """Decorator to require authentication for routes"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_current_session():
            return redirect(url_for('login', expired='true'))
        return f(*args, **kwargs)

    return decorated_function


# @app.route('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with TOTP authentication - using modular API"""
    from api.auth_api import handle_login_post, handle_login_get
    
    if request.method == 'POST':
        redirect_response, template_response = handle_login_post(neo_client, user_manager)
        return redirect_response if redirect_response else template_response
    else:
        return handle_login_get()


@app.route('/logout')
def logout():
    """Logout and clear session - using modular API"""
    from api.auth_api import handle_logout
    return handle_logout()


@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with portfolio overview - using modular API"""
    from api.dashboard_api import handle_dashboard_page
    return handle_dashboard_page(trading_functions)


@app.route('/positions')
@require_auth
def show_positions():
    return positions()


@app.route('/holdings')
@require_auth
def show_holdings():
    return holdings()


@app.route('/orders')
@require_auth
def show_orders():
    return orders()


@app.route('/charts')
@require_auth
def charts():
    """Charts page for trading analysis"""

    return render_template('charts.html')


# ETF signals route is handled by main blueprint in routes/main.py


@app.route('/etf-signals-advanced')
@require_auth
def etf_signals_advanced():
    """Advanced ETF Trading Signals page with datatable"""
    return render_template('etf_signals_datatable.html')


@app.route('/default-deals')
def default_deals():
    """Default Deals page"""
    return render_template('default_deals.html')


@app.route('/admin-signals-datatable')
@require_auth
def admin_signals_datatable():
    """Admin Trade Signals Datatable with Kotak Neo integration"""
    return render_template('admin_signals_datatable.html')


@app.route('/admin-signals')
@require_auth
def admin_signals():
    """Admin Panel for managing trading signals with advanced datatable"""
    return render_template('admin_signals_datatable.html')


@app.route('/admin-signals-basic')
@require_auth
def admin_signals_basic():
    """Basic Admin Panel for sending trading signals"""
    return render_template('admin_signals.html')


@app.route('/basic-trade-signals')
@require_auth
def basic_trade_signals():
    """Basic Trade Signals page"""
    return render_template('basic_etf_signals.html')


# API endpoints
@app.route('/api/dashboard-data')
def get_dashboard_data_api():
    """AJAX endpoint for dashboard data without page refresh"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:

        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        dashboard_data = trading_functions.get_dashboard_data(client)
        return jsonify(dashboard_data)
    except Exception as e:
        logging.error(f"Dashboard data error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/holdings')
def get_holdings_api():
    """API endpoint to get holdings"""
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        holdings = trading_functions.get_holdings(client)
        return jsonify(holdings)
    except Exception as e:
        logging.error(f"Holdings API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/etf-signals-data')
def get_etf_signals_data():
    """API endpoint to get ETF signals data from external admin_trade_signals table"""
    try:
        from Scripts.external_db_service import get_etf_signals_data_json
        return jsonify(get_etf_signals_data_json())
    except Exception as e:
        logging.error(f"ETF signals API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/basic-trade-signals-data')
def get_basic_trade_signals_data():
    """API endpoint to get basic trade signals data from external admin_trade_signals table"""
    try:
        from Scripts.external_db_service import get_basic_trade_signals_data_json
        return jsonify(get_basic_trade_signals_data_json())
    except Exception as e:
        logging.error(f"Basic trade signals API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync-default-deals', methods=['POST'])
def sync_default_deals_endpoint():
    """API endpoint to sync all admin_trade_signals to default_deals table"""
    try:
        synced_count = sync_admin_signals_to_default_deals()

        return jsonify({
            'success': True,
            'message':
            f'Successfully synced {synced_count} admin signals to default deals',
            'synced_count': synced_count
        })

    except Exception as e:
        logging.error(f"Error in sync default deals endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/default-deals-data')
def get_default_deals_data():
    """API endpoint to get default deals data directly from admin_trade_signals - using modular API"""
    from api.signals_api import handle_default_deals_data_logic
    return handle_default_deals_data_logic()


@app.route('/api/initialize-auto-sync', methods=['POST'])
def initialize_auto_sync_endpoint():
    """API endpoint to initialize automatic synchronization system"""
    try:
        from Scripts.auto_sync_system import initialize_auto_sync_system
        result = initialize_auto_sync_system()

        return jsonify({
            'success':
            result['success'],
            'message':
            'Auto-sync system initialized successfully'
            if result['success'] else 'Failed to initialize auto-sync system',
            'details':
            result
        })

    except Exception as e:
        logging.error(f"Error initializing auto-sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/place-order', methods=['POST'])
@require_auth
def place_order():
    """API endpoint to place buy/sell orders using Kotak Neo API - using modular API"""
    from api.trading_api import handle_place_order_logic
    from Scripts.neo_client import NeoClient
    
    neo_client = NeoClient()
    return handle_place_order_logic(trading_functions, neo_client)


@app.route('/api/quick-buy', methods=['POST'])
@require_auth
def quick_buy():
    """Quick buy order for holdings/default-deals pages"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity', '1')
        price = data.get('price', '0')
        order_type = data.get('order_type', 'MARKET')

        # Get client from session
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        from Scripts.trading_functions import TradingFunctions
        trading_functions = TradingFunctions()

        order_params = {
            'symbol': symbol,
            'quantity': quantity,
            'transaction_type': 'B',  # Buy
            'order_type': order_type,
            'price': price,
            'exchange_segment': 'nse_cm',
            'product': 'CNC',
            'validity': 'DAY'
        }

        result = trading_functions.place_order(client, order_params)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'Buy order placed successfully for {symbol}',
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success':
                False,
                'message':
                result.get('message', 'Failed to place buy order')
            }), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/quick-sell', methods=['POST'])
@require_auth
def quick_sell():
    """Quick sell order for holdings/default-deals pages"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity', '1')
        price = data.get('price', '0')
        order_type = data.get('order_type', 'MARKET')

        # Get client from session
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        from Scripts.trading_functions import TradingFunctions
        trading_functions = TradingFunctions()

        order_params = {
            'symbol': symbol,
            'quantity': quantity,
            'transaction_type': 'S',  # Sell
            'order_type': order_type,
            'price': price,
            'exchange_segment': 'nse_cm',
            'product': 'CNC',
            'validity': 'DAY'
        }

        result = trading_functions.place_order(client, order_params)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'Sell order placed successfully for {symbol}',
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success':
                False,
                'message':
                result.get('message', 'Failed to place sell order')
            }), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Google Finance and Yahoo Finance schedulers removed

from routes.auth import auth_bp
from routes.main import main_bp
from api.dashboard import dashboard_api
from api.trading import trading_api
from Scripts.sync_default_deals import sync_admin_signals_to_default_deals, update_default_deal_from_admin_signal
from Scripts.auto_sync_triggers import initialize_auto_sync
from Scripts.models import DefaultDeal
# ETF signals blueprint will be registered separately

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(dashboard_api, url_prefix='/api')
app.register_blueprint(trading_api, url_prefix='/api')

# ETF Signals functionality will be handled by the blueprint

# Additional blueprints
try:
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.notifications import notifications_bp
    from api.realtime_quotes import quotes_bp
    from api.signals_datatable import datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp
    from api.admin_signals_api import admin_signals_bp
    from api.deals import deals_bp  # Added deals blueprint import
    # Google Finance, Yahoo Finance, and Supabase APIs removed

    # Blueprint registration moved to main.py to avoid conflicts
    print("✓ Blueprint imports available")

    # Initialize realtime quotes scheduler
    try:
        from Scripts.realtime_quotes_manager import start_quotes_scheduler
        start_quotes_scheduler()
        print("✓ Realtime quotes scheduler started")
    except Exception as e:
        print(f"Warning: Could not start quotes scheduler: {e}")

except ImportError as e:
    print(f"Warning: Could not import additional blueprint: {e}")

    # Register deals blueprint
    try:
        from api.deals import deals_bp
        app.register_blueprint(deals_bp, url_prefix='/api/deals')
        print("✓ Deals blueprint registered")
    except Exception as e:
        print(f"Warning: Could not register deals blueprint: {e}")

    # Register ETF signals blueprint
    app.register_blueprint(etf_bp, url_prefix='/api')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Start ETF data scheduler for real-time quotes
    try:
        from Scripts.etf_data_scheduler import start_etf_data_scheduler
        start_etf_data_scheduler()
        logging.info("✅ ETF Data Scheduler initialized")
    except Exception as e:
        logging.error(f"❌ Failed to start ETF scheduler: {str(e)}")

    # Initialize admin signals scheduler for comprehensive Kotak Neo data updates (5-minute intervals)
    try:
        logging.info(
            "Starting admin signals scheduler with Kotak Neo integration...")
        from Scripts.admin_signals_scheduler import start_admin_signals_scheduler
        start_admin_signals_scheduler()
        logging.info(
            "✅ Admin signals scheduler started - automatic updates every 5 minutes"
        )
    except Exception as e:
        logging.error(f"❌ Failed to start admin signals scheduler: {e}")

# Initialize auto-sync triggers
from Scripts.sync_default_deals import setup_auto_sync_triggers

setup_auto_sync_triggers()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)