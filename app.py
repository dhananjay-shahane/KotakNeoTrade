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

# Add current directory to Python path for module imports
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        return redirect(url_for('auth_routes.login'))

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


# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    try:
        import Scripts.models as models  # noqa: F401
        import Scripts.models_etf as models_etf  # noqa: F401
        print("Database tables created successfully")
    except ImportError as e:
        print(f"Database initialization optional: {e}")

    db.create_all()

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
try:
    from Scripts.neo_client import NeoClient
    from Scripts.trading_functions import TradingFunctions
    from Scripts.user_manager import UserManager
    from Scripts.session_helper import SessionHelper
    from Scripts.websocket_handler import WebSocketHandler

    neo_client = NeoClient()
    trading_functions = TradingFunctions()
    user_manager = UserManager()
    session_helper = SessionHelper()
    websocket_handler = WebSocketHandler()
    print("Trading platform components initialized")
except ImportError as e:
    print(f"Trading components optional: {e}")

# Supabase integration removed
supabase_client = None
logging.info("✅ Using local PostgreSQL database only")


def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Use the core auth validation function
        from core.auth import validate_current_session as core_validate
        return core_validate()
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


def get_kotak_account_data():
    """Get Kotak account data for sidebar if user is logged in"""
    if session.get('kotak_logged_in'):
        return {
            'ucc': session.get('ucc', '-'),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', 'User'),
            'last_login': 'Just Now',
            'status': 'Online'
        }
    return None


# ========================================
# TRADING PLATFORM ROUTES
# ========================================

# Functions imports for trading functionality
try:
    from functions.positions.positions import positions
    from functions.holdings.holdings import holdings
    from functions.orders.orders import orders
    from functions.dashboard.dashboard import dashboard
    from functions.dashboard.dashboard_data import get_dashboard_data_api
except ImportError as e:
    print(f"Trading functions optional: {e}")

# Add Kotak Neo dashboard route
@app.route('/dashboard')
def show_dashboard():
    """Kotak Neo dashboard route - render dashboard directly"""
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))
    
    # Prepare account data for sidebar
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc': session.get('ucc', session.get('username', '-')),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', session.get('username', 'User')),
            'last_login': 'Just Now',
            'status': 'Online'
        }
    
    # Render dashboard with empty data structure for now
    dashboard_data = {
        'positions': [],
        'holdings': [],
        'limits': {},
        'recent_orders': [],
        'total_positions': 0,
        'total_holdings': 0,
        'total_orders': 0
    }
    
    return render_template('dashboard.html', data=dashboard_data, kotak_account=kotak_account_data)

# Add missing Kotak Neo routes that are referenced in the sidebar - render directly to avoid redirect loops
@app.route('/orders')
def orders_redirect():
    """Kotak Neo orders route"""
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))
    
    # Prepare account data for sidebar
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc': session.get('ucc', session.get('username', '-')),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', session.get('username', 'User')),
            'last_login': 'Just Now',
            'status': 'Online'
        }
    
    return render_template('orders.html', kotak_account=kotak_account_data, page_title="Orders")

@app.route('/positions')  
def positions_redirect():
    """Kotak Neo positions route"""  
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))
    
    # Prepare account data for sidebar
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc': session.get('ucc', session.get('username', '-')),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', session.get('username', 'User')),
            'last_login': 'Just Now',
            'status': 'Online'
        }
    
    return render_template('positions.html', kotak_account=kotak_account_data, page_title="Positions")

# Remove duplicate route - using show_holdings below instead


@app.route('/')
def index():
    """Home page - redirect to portfolio if authenticated, else to login"""
    # Check if user is authenticated
    if session.get('authenticated') or session.get('kotak_logged_in'):
        return redirect(url_for('portfolio'))
    else:
        return redirect(url_for('auth_routes.trading_account_login'))


@app.route('/portfolio')
def portfolio():
    """Portfolio page - show portfolio.html template"""
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))
    
    # Prepare Kotak account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc': session.get('ucc', session.get('username', '-')),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', session.get('username', 'User')),
            'last_login': 'Just Now',
            'status': 'Online'
        }
    
    return render_template('portfolio.html', kotak_account=kotak_account_data)


@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page"""
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare Kotak account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in'):
        kotak_account_data = {
            'ucc': session.get('ucc', '-'),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', 'User'),
            'last_login': 'Just Now',
            'status': 'Online'
        }

    return render_template('trading_signals.html',
                           kotak_account=kotak_account_data)


@app.route('/deals')
def deals():
    """Deals page"""
    # Check if user is authenticated
    if not session.get('authenticated') and not session.get('kotak_logged_in'):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare Kotak account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in'):
        kotak_account_data = {
            'ucc': session.get('ucc', '-'),
            'mobile': session.get('mobile_number', '-'),
            'greeting_name': session.get('greeting_name', 'User'),
            'last_login': 'Just Now',
            'status': 'Online'
        }

    return render_template('deals.html', kotak_account=kotak_account_data)


@app.route('/positions')
def show_positions():
    # Check if user is authenticated with any login method
    if not (session.get('authenticated') or session.get('kotak_logged_in')):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc':
            session.get('ucc', session.get('username', '-')),
            'mobile':
            session.get('mobile_number', '-'),
            'greeting_name':
            session.get('greeting_name', session.get('username', 'User')),
            'last_login':
            'Just Now',
            'status':
            'Online'
        }

    try:
        return positions()
    except:
        return render_template('positions.html',
                               kotak_account=kotak_account_data)


@app.route('/holdings')
def show_holdings():
    # Check if user is authenticated with any login method
    if not (session.get('authenticated') or session.get('kotak_logged_in')):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc':
            session.get('ucc', session.get('username', '-')),
            'mobile':
            session.get('mobile_number', '-'),
            'greeting_name':
            session.get('greeting_name', session.get('username', 'User')),
            'last_login':
            'Just Now',
            'status':
            'Online'
        }

    # Try to get holdings data from API client if available
    holdings_data = []
    try:
        client = session.get('client')
        if client:
            from Scripts.trading_functions import TradingFunctions
            trading_funcs = TradingFunctions()
            holdings_response = trading_funcs.get_holdings(client)
            if isinstance(holdings_response, list):
                holdings_data = holdings_response
            elif isinstance(holdings_response, dict) and 'holdings' in holdings_response:
                holdings_data = holdings_response['holdings']
            elif isinstance(holdings_response, dict) and 'error' in holdings_response:
                logging.error(f"Holdings API error: {holdings_response['error']}")
            logging.info(f"Holdings data fetched for template: {len(holdings_data)} items")
    except Exception as e:
        logging.error(f"Error fetching holdings for template: {e}")
    
    return render_template('holdings.html', kotak_account=kotak_account_data, holdings=holdings_data)


@app.route('/orders')
def show_orders():
    # Check if user is authenticated with any login method
    if not (session.get('authenticated') or session.get('kotak_logged_in')):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc':
            session.get('ucc', session.get('username', '-')),
            'mobile':
            session.get('mobile_number', '-'),
            'greeting_name':
            session.get('greeting_name', session.get('username', 'User')),
            'last_login':
            'Just Now',
            'status':
            'Online'
        }

    try:
        return orders()
    except:
        return render_template('orders.html', kotak_account=kotak_account_data)


@app.route('/charts')
def show_charts():
    # Check if user is authenticated with any login method
    if not (session.get('authenticated') or session.get('kotak_logged_in')):
        return redirect(url_for('auth_routes.trading_account_login'))

    # Prepare account data for sidebar if logged in
    kotak_account_data = None
    if session.get('kotak_logged_in') or session.get('authenticated'):
        kotak_account_data = {
            'ucc':
            session.get('ucc', session.get('username', '-')),
            'mobile':
            session.get('mobile_number', '-'),
            'greeting_name':
            session.get('greeting_name', session.get('username', 'User')),
            'last_login':
            'Just Now',
            'status':
            'Online'
        }

    try:
        return render_template('charts.html', kotak_account=kotak_account_data)
    except:
        return render_template('charts.html', kotak_account=kotak_account_data)


@app.route('/basic-trade-signals')
@require_auth
def basic_trade_signals():
    """Basic Trade Signals page"""
    return render_template('basic_etf_signals.html')


# ========================================
# API ENDPOINTS
# ========================================


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


@app.route('/api/positions')
def get_positions_api():
    """API endpoint to get positions"""
    if not validate_current_session():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'error': 'No active client'}), 400

        positions = trading_functions.get_positions(client)
        
        # Ensure positions is always a list and return in expected format
        if isinstance(positions, dict) and 'positions' in positions:
            positions_list = positions['positions']
        elif isinstance(positions, list):
            positions_list = positions
        else:
            positions_list = []
            
        return jsonify({
            'success': True,
            'positions': positions_list,
            'count': len(positions_list)
        })
    except Exception as e:
        logging.error(f"Positions API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/holdings')
def get_holdings_api():
    """API endpoint to get holdings"""
    if not validate_current_session():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'error': 'No active client'}), 400

        holdings = trading_functions.get_holdings(client)
        
        # Ensure holdings is always a list and return in expected format
        if isinstance(holdings, dict) and 'holdings' in holdings:
            holdings_list = holdings['holdings']
        elif isinstance(holdings, list):
            holdings_list = holdings
        else:
            holdings_list = []
            
        return jsonify({
            'success': True,
            'holdings': holdings_list,
            'count': len(holdings_list)
        })
    except Exception as e:
        logging.error(f"Holdings API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders')
def get_orders_api():
    """API endpoint to get orders"""
    if not validate_current_session():
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'error': 'No active client'}), 400

        orders = trading_functions.get_orders(client)
        
        # Ensure orders is always a list and return in expected format
        if isinstance(orders, dict) and 'orders' in orders:
            orders_list = orders['orders']
        elif isinstance(orders, list):
            orders_list = orders
        else:
            orders_list = []
            
        return jsonify({
            'success': True,
            'orders': orders_list,
            'count': len(orders_list)
        })
    except Exception as e:
        logging.error(f"Orders API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/etf-signals-data')
def get_etf_signals_data():
    """API endpoint to get ETF signals data from external database with pagination"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        # Check if database credentials are available first
        import os
        db_host = os.getenv('DB_HOST')
        database_url = os.getenv('DATABASE_URL')

        if not database_url and not db_host:
            # No credentials configured
            return jsonify({
                'success':
                False,
                'data': [],
                'recordsTotal':
                0,
                'recordsFiltered':
                0,
                'page':
                page,
                'has_more':
                False,
                'error':
                'Database credentials not configured',
                'message':
                'Please configure database credentials (DATABASE_URL or DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) to access trading data.'
            }), 200

        # Try to get real data from external database with pagination
        from Scripts.external_db_service import get_etf_signals_data_json
        result = get_etf_signals_data_json(page, page_size)
        return jsonify(result)

    except Exception as e:
        logging.error(f"ETF signals API error: {e}")
        return jsonify({
            'success':
            False,
            'data': [],
            'recordsTotal':
            0,
            'recordsFiltered':
            0,
            'page':
            1,
            'has_more':
            False,
            'error':
            f'Database connection failed: {str(e)}',
            'message':
            'Cannot connect to trading database. Please verify your database credentials are correct.'
        }), 200


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
        from Scripts.sync_default_deals import sync_admin_signals_to_default_deals
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
    try:
        from api.signals_api import handle_default_deals_data_logic
        return handle_default_deals_data_logic()
    except Exception as e:
        logging.error(f"Default deals API error: {e}")
        return jsonify({'error': str(e)}), 500


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
    try:
        from api.trading_api import handle_place_order_logic
        from Scripts.neo_client import NeoClient

        neo_client = NeoClient()
        return handle_place_order_logic(trading_functions, neo_client)
    except Exception as e:
        logging.error(f"Place order API error: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================
# BLUEPRINT REGISTRATION
# ========================================

# Import blueprints
try:
    from routes.auth_routes import auth_bp as auth_routes_bp
    from routes.main_routes import main_bp as main_routes_bp
    from api.dashboard import dashboard_api
    from api.trading import trading_api

    # Register blueprints with consistent naming
    app.register_blueprint(auth_routes_bp)
    app.register_blueprint(main_routes_bp)
    app.register_blueprint(dashboard_api, url_prefix='/api')
    app.register_blueprint(trading_api, url_prefix='/api')
    print("✓ Core blueprints registered")
except ImportError as e:
    print(f"Core blueprint registration optional: {e}")

# Register additional blueprints
try:
    from api.user_deals_api import user_deals_bp
    app.register_blueprint(user_deals_bp, url_prefix='/api')
    print("✓ Deals blueprint registered")
except Exception as e:
    print(f"Warning: Could not register deals blueprint: {e}")

# Additional blueprints
try:
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.notifications import notifications_bp
    from api.realtime_quotes import quotes_bp
    from api.signals_datatable import datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp
    from api.admin_signals_api import admin_signals_bp

    # Register ETF signals blueprint
    app.register_blueprint(etf_bp, url_prefix='/api')
    print("✓ Additional blueprints available")

    # Initialize realtime quotes scheduler
    try:
        from Scripts.realtime_quotes_manager import start_quotes_scheduler
        start_quotes_scheduler()
        print("✓ Realtime quotes scheduler started")
    except Exception as e:
        print(f"Warning: Could not start quotes scheduler: {e}")

except ImportError as e:
    print(f"Warning: Could not import additional blueprint: {e}")

# Register deals blueprint directly
try:
    from api.deals_api import deals_api
    app.register_blueprint(deals_api)
    print("✓ Registered deals_api blueprint directly")
except Exception as e:
    print(f"✗ Error registering deals_api: {e}")

# Initialize auto-sync triggers
try:
    from Scripts.sync_default_deals import setup_auto_sync_triggers
    setup_auto_sync_triggers()
    print("✓ Auto-sync triggers initialized")
except Exception as e:
    print(f"Auto-sync setup optional: {e}")

# ========================================
# KOTAK NEO PROJECT INTEGRATION
# ========================================

# Register Kotak Neo blueprints
try:
    from kotak_neo_project.app import app as kotak_app

    # Copy routes from Kotak Neo app to main app
    for rule in kotak_app.url_map.iter_rules():
        if rule.endpoint not in app.view_functions:
            app.add_url_rule(f"/kotak{rule.rule}",
                             endpoint=f"kotak_{rule.endpoint}",
                             view_func=kotak_app.view_functions[rule.endpoint],
                             methods=rule.methods)

    print("Successfully registered Kotak Neo blueprints")
except Exception as e:
    print(f"Kotak Neo integration optional: {e}")

# ========================================
# APPLICATION STARTUP
# ========================================

# Email functionality preserved from original code
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize extensions for email functionality
try:
    mail = Mail(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    print("✓ Email and login extensions initialized")
except Exception as e:
    print(f"Email extensions optional: {e}")

# Define User model for login functionality
try:

    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(100), unique=True, nullable=False)
        mobile = db.Column(db.String(20), unique=True, nullable=False)
        username = db.Column(db.String(50), unique=True, nullable=False)
        password_hash = db.Column(db.String(128), nullable=False)
        registration_date = db.Column(db.DateTime, default=datetime.utcnow)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    print("✓ User model defined")
except Exception as e:
    print(f"User model optional: {e}")

# Email configuration for registration functionality
try:
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME',
                                                 'your-email@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD',
                                                 'your-app-password')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER',
                                                       'your-email@gmail.com')
    print("✓ Email configuration loaded")
except Exception as e:
    print(f"Email configuration optional: {e}")


def send_registration_email(user_email, username, password):
    """Send registration confirmation email with credentials"""
    try:
        msg = Message(
            subject="Welcome to Trading Platform - Your Account Details",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email])

        # Email content (simplified for brevity)
        msg.html = f"""
        <h2>Welcome to Trading Platform!</h2>
        <p>Your login credentials:</p>
        <ul>
            <li>Username: {username}</li>
            <li>Password: {password}</li>
            <li>Email: {user_email}</li>
        </ul>
        <p>Please keep these credentials safe and secure.</p>
        """

        msg.body = f"""
        Welcome to Trading Platform!

        Login Credentials:
        Username: {username}
        Password: {password}
        Email: {user_email}

        Please keep these credentials safe and secure.
        """

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Registration and login routes preserved from original code
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate input
        if not all([email, mobile, username, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        # Check if user already exists
        try:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken.', 'error')
                return render_template('auth/register.html')

            # Create new user
            user = User(email=email, mobile=mobile, username=username)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            # Send registration email with credentials
            email_sent = send_registration_email(email, username, password)

            if email_sent:
                flash(
                    'Registration successful! Please check your email for login credentials.',
                    'success')
            else:
                flash(
                    'Registration successful! However, we couldn\'t send the confirmation email. Please note your credentials.',
                    'warning')

            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('portfolio'))
            else:
                flash('Invalid username or password.', 'error')
                return render_template('auth/login.html')
        except Exception as e:
            flash('Login error. Please try again.', 'error')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))


# ========================================
# APPLICATION INITIALIZATION
# ========================================

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

    # Initialize admin signals scheduler for comprehensive Kotak Neo data updates
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

    # Ensure the instance folder exists for SQLite fallback
    try:
        os.makedirs(os.path.dirname('instance/trading_platform.db'),
                    exist_ok=True)
    except Exception as e:
        pass

    app.run(host='0.0.0.0', port=5000, debug=True)
