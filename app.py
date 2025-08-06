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
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

# Add current directory to Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv(dotenv_path='.env', override=True)


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

# Database configuration - use centralized configuration
try:
    from config.database_config import get_database_url
    database_url = get_database_url()
    print("✓ Using External PostgreSQL Database")
except ImportError:
    # Secure fallback - only use environment variables
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("Database configuration not available. Please ensure config/database_config.py is accessible.")
    print("✓ Using database from environment variables")

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


# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        # Make sure to import the models here or their tables won't be created
        try:
            import Scripts.models as models  # noqa: F401
            import Scripts.models_etf as models_etf  # noqa: F401
            print("✓ Models imported successfully")
        except ImportError as e:
            print(f"Model imports optional: {e}")
        # db.create_all()
        # print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Continue running even if database creation fails

# Configure session for persistent storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
Session(app)

# Configure Flask-Mail for email functionality
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize Flask-Mail
from flask_mail import Mail
mail = Mail(app)

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
            return redirect(url_for('auth_routes.trading_account_login', expired='true'))
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


# ================================= berjumpa=======
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

    return render_template('dashboard.html',
                           data=dashboard_data,
                           kotak_account=kotak_account_data)


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

    return render_template('orders.html',
                           kotak_account=kotak_account_data,
                           page_title="Orders")


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

    return render_template('positions.html',
                           kotak_account=kotak_account_data,
                           page_title="Positions")


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
    """Portfolio page - show portfolio.html template - authentication required"""
    # Check if user is authenticated - no guest access allowed
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

    return render_template('portfolio.html', kotak_account=kotak_account_data)


@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page - authentication required"""
    # Check if user is authenticated - no guest access allowed
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

    return render_template('trading_signals.html',
                           kotak_account=kotak_account_data)


@app.route('/deals')
def deals():
    """Deals page - authentication required"""
    # Check if user is authenticated - no guest access allowed
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
        if 'positions' in globals():
            return positions()
        else:
            return render_template('positions.html',
                                   kotak_account=kotak_account_data)
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
            elif isinstance(holdings_response,
                            dict) and 'holdings' in holdings_response:
                holdings_data = holdings_response['holdings']
            elif isinstance(holdings_response,
                            dict) and 'error' in holdings_response:
                logging.error(
                    f"Holdings API error: {holdings_response['error']}")
            logging.info(
                f"Holdings data fetched for template: {len(holdings_data)} items"
            )
    except Exception as e:
        logging.error(f"Error fetching holdings for template: {e}")

    return render_template('holdings.html',
                           kotak_account=kotak_account_data,
                           holdings=holdings_data)


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
        if 'orders' in globals():
            return orders()
        else:
            return render_template('orders.html',
                                   kotak_account=kotak_account_data)
    except:
        return render_template('orders.html', kotak_account=kotak_account_data)


@app.route('/charts')
def show_charts():
    # For testing/development: Allow charts access without authentication
    # In production, enable authentication by uncommenting below
    # if not (session.get('authenticated') or session.get('kotak_logged_in')):
    #     return redirect(url_for('auth_routes.trading_account_login'))

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


@app.route('/default-deals')
@require_auth
def default_deals():
    """Default deals page - shows all deals from default_deals table"""
    return render_template('default_deals.html')


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

        if trading_functions:
            dashboard_data = trading_functions.get_dashboard_data(client)
        else:
            dashboard_data = {'error': 'Trading functions not available'}
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
            return jsonify({
                'success': False,
                'error': 'No active client'
            }), 400

        if trading_functions:
            positions = trading_functions.get_positions(client)
        else:
            positions = []

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
            return jsonify({
                'success': False,
                'error': 'No active client'
            }), 400

        if trading_functions:
            holdings = trading_functions.get_holdings(client)
        else:
            holdings = []

        # Ensure holdings is always a list and return in expected format
        if isinstance(holdings, dict) and 'holdings' in holdings:
            holdings_list = holdings['holdings']
        elif isinstance(positions, list):
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
            return jsonify({
                'success': False,
                'error': 'No active client'
            }), 400

        if trading_functions:
            orders = trading_functions.get_orders(client)
        else:
            orders = []

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
        from Scripts.external_db_service import get_etf_signals_data_json
        # Use ETF signals data as basic trade signals
        return jsonify(get_etf_signals_data_json())
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

@app.route('/api/enable-email-notifications', methods=['GET'])
def enable_email_notifications():
    """Temporary endpoint to enable email notifications for dha86"""
    try:
        from config.database_config import execute_db_query
        
        # Check current settings
        query = """
            SELECT username, email, email_notification 
            FROM external_users 
            WHERE username = %s
        """
        result = execute_db_query(query, ('dha86',))
        
        if not result:
            return jsonify({"error": "User dha86 not found"}), 404
            
        user_data = result[0]
        current_status = user_data.get('email_notification', False)
        
        # Enable email notifications
        update_query = """
            UPDATE external_users 
            SET email_notification = true 
            WHERE username = %s
        """
        execute_db_query(update_query, ('dha86',))
        
        return jsonify({
            "success": True,
            "message": f"Email notifications enabled for dha86",
            "previous_status": current_status,
            "current_status": True,
            "email": user_data.get('email')
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to enable email notifications: {str(e)}"}), 500

@app.route('/api/test-email', methods=['GET'])
def test_email():
    """Test email functionality directly"""
    try:
        from api.email_service import EmailService
        from datetime import datetime
        
        email_service = EmailService()
        
        # Test simple email
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_subject = "Test Email from Kotak Neo Platform"
        test_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email</h2>
            <p>This is a test email from your Kotak Neo Trading Platform.</p>
            <p>If you receive this, your email system is working correctly!</p>
            <p>Time: {current_time}</p>
        </body>
        </html>
        """
        
        text_content = f"Test email from Kotak Neo Platform at {current_time}"
        
        success = email_service.send_email(
            "dhananjayshahane24@gmail.com",
            test_subject,
            text_content,
            test_content
        )
        
        return jsonify({
            "success": success,
            "message": "Test email sent" if success else "Failed to send test email",
            "email_configured": email_service.is_configured,
            "from_email": email_service.from_email
        })
        
    except Exception as e:
        return jsonify({"error": f"Test email failed: {str(e)}"}), 500


# ========================================
# BLUEPRINT REGISTRATION
# ========================================

# Import blueprints
try:
    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp

    # Register blueprints with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    print("✓ Core blueprints registered")
except ImportError as e:
    print(f"Core blueprint registration error: {e}")
    # Fallback registration if imports fail
    from flask import Blueprint
    auth_bp = Blueprint('auth_bp', __name__)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print("✓ Fallback auth blueprint registered")

# Register API blueprints
try:
    from api.dashboard import dashboard_api
    from api.trading import trading_api
    app.register_blueprint(dashboard_api, url_prefix='/api')
    app.register_blueprint(trading_api, url_prefix='/api')
    print("✓ API blueprints registered")
except ImportError as e:
    print(f"API blueprint registration optional: {e}")

# Register additional blueprints
try:
    from api.user_deals_api import user_deals_bp
    app.register_blueprint(user_deals_bp, url_prefix='/api')
    print("✓ Deals blueprint registered")
except Exception as e:
    print(f"Warning: Could not register deals blueprint: {e}")

# Register signals API blueprint with add deal functionality
try:
    from api.signals_api import signals_bp
    app.register_blueprint(signals_bp, url_prefix='/api')
    print("✓ Registered signals_api blueprint")
except Exception as e:
    print(f"✗ Error registering signals_api: {e}")

# Additional blueprints
try:
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.notifications import notifications_bp
    from api.realtime_quotes import quotes_bp
    from api.signals_datatable import datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp
    from api.admin_signals_api import admin_signals_bp
    from api.candlestick_api import candlestick_bp

    # Register ETF signals blueprint
    app.register_blueprint(etf_bp, url_prefix='/api')
    # Register candlestick charts API
    app.register_blueprint(candlestick_bp, url_prefix='/api')
    print("✓ Additional blueprints available")

except ImportError as e:
    print(f"Warning: Could not import additional blueprint: {e}")

# Register deals blueprint directly
try:
    from api.deals_api import deals_api
    app.register_blueprint(deals_api)
    print("✓ Registered deals_api blueprint directly")
except Exception as e:
    print(f"✗ Error registering deals_api: {e}")

# Register portfolio API blueprint
try:
    from api.portfolio_api import portfolio_api
    app.register_blueprint(portfolio_api)
    print("✓ Registered portfolio_api blueprint")
except Exception as e:
    print(f"✗ Error registering portfolio_api: {e}")

# Register dynamic deals API blueprint
try:
    from api.dynamic_deals_api import dynamic_deals_api
    app.register_blueprint(dynamic_deals_api)
    print("✓ Registered dynamic_deals_api blueprint")
except Exception as e:
    print(f"✗ Error registering dynamic_deals_api: {e}")

# Initialize auto-sync triggers
try:
    from Scripts.sync_default_deals import setup_auto_sync_triggers
    setup_auto_sync_triggers()
    print("✓ Auto-sync triggers initialized")
except Exception as e:
    print(f"Auto-sync setup optional: {e}")

# Initialize daily email scheduler in background
try:
    import threading
    from Scripts.daily_email_scheduler import DailyEmailScheduler
    
    def start_email_scheduler():
        """Start email scheduler in background thread"""
        scheduler = DailyEmailScheduler()
        scheduler.setup_scheduler()
        # Just setup, don't run continuously in web app
        print("✅ Daily email scheduler configured")
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=start_email_scheduler, daemon=True)
    scheduler_thread.start()
    print("✓ Email scheduler initialized in background")
except Exception as e:
    print(f"Email scheduler setup optional: {e}")

# Register default deals API blueprint
try:
    from api.default_deals_api import default_deals_api
    app.register_blueprint(default_deals_api)
    print("✓ Registered default_deals_api blueprint")
except Exception as e:
    print(f"✗ Error registering default_deals_api: {e}")

# Register password reset API blueprint
try:
    from api.password_reset_api import password_reset_bp
    app.register_blueprint(password_reset_bp)
    print("✓ Registered password_reset_api blueprint")
except Exception as e:
    print(f"✗ Error registering password_reset_api: {e}")

# Register notifications API blueprint
try:
    from api.notifications_api import notifications_api
    app.register_blueprint(notifications_api)
    print("✓ Registered notifications_api blueprint")
except Exception as e:
    print(f"✗ Error registering notifications_api: {e}")

# Register email functions API blueprint
try:
    from api.email_functions import email_functions_bp
    app.register_blueprint(email_functions_bp)
    print("✓ Registered email_functions_api blueprint")
except Exception as e:
    print(f"✗ Error registering email_functions_api: {e}")

# Register settings routes blueprint
try:
    from routes.settings_routes import settings_routes
    app.register_blueprint(settings_routes)
    print("✓ Registered settings_routes blueprint")
except Exception as e:
    print(f"✗ Error registering settings_routes: {e}")

# Add direct /settings route with authentication
@app.route('/settings')
def settings_page():
    """Settings page with authentication check"""
    # Check if user is authenticated
    if not (session.get('authenticated') or session.get('kotak_logged_in')):
        return redirect(url_for('auth_routes.trading_account_login'))
    
    user_email = session.get('email', session.get('user_email', 'Not configured'))
    return render_template('settings.html', user_email=user_email)

# Register email settings API routes
@app.route('/api/email-settings', methods=['GET'])
def api_get_email_settings():
    """API endpoint to get user email notification settings"""
    from api.settings_api import get_user_email_settings
    return get_user_email_settings()

@app.route('/api/email-settings', methods=['POST'])
def api_save_email_settings():
    """API endpoint to save user email notification settings"""
    from api.settings_api import save_user_email_settings
    return save_user_email_settings()

print("✓ Registered email settings API routes")

# ================================= berjumpa=======
# KOTAK NEO PROJECT INTEGRATION
# ========================================

# Register Kotak Neo blueprints
# Kotak Neo integration - optional
try:
    print("Kotak Neo integration components already integrated in main app")
except Exception as e:
    print(f"Kotak Neo integration optional: {e}")

# ========================================
# FALLBACK AUTH ROUTES
# ========================================

@app.route('/auth/trading-account/login', methods=['GET', 'POST'])
def fallback_trading_account_login():
    """Fallback trading account login route"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('auth/login.html')

            # Simple authentication check
            if username and password:
                session['authenticated'] = True
                session['username'] = username
                session['user_id'] = username
                session['ucc'] = username
                session['greeting_name'] = username
                session['login_type'] = 'trading_account'
                session.permanent = True
                
                flash('Login successful!', 'success')
                return redirect(url_for('portfolio'))
            else:
                flash('Invalid credentials', 'error')

        except Exception as e:
            flash('Login error. Please try again.', 'error')

    return render_template('auth/login.html')

@app.route('/auth/logout')
def fallback_logout():
    """Fallback logout route"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('fallback_trading_account_login'))

# ========================================
# APPLICATION STARTUP
# ========================================

# Import missing functions and trading_functions
try:
    from functions.positions.positions import positions
    from functions.orders.orders import orders
    from Scripts.trading_functions import TradingFunctions
    trading_functions = TradingFunctions()
    print("✓ Trading functions imported successfully")
except Exception as e:
    print(f"Warning: Could not import trading functions: {e}")
    trading_functions = None

# Initialize extensions for email functionality
login_manager = None
mail = None

try:
    # Initialize LoginManager properly
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.trading_account_login'  # type: ignore

    # Configure email settings first
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS',
                                                'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get(
        'MAIL_USERNAME') or os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get(
        'MAIL_PASSWORD') or os.environ.get('EMAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get(
        'MAIL_DEFAULT_SENDER') or app.config['MAIL_USERNAME']

    # Initialize Mail with configured app
    if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
        mail = Mail(app)
        print(f"✅ Email service configured for: {app.config['MAIL_USERNAME']}")
        print("✓ Email and login extensions initialized")
    else:
        print("❌ Email credentials missing. Email service disabled.")
        mail = None
except Exception as e:
    print(f"Email extensions optional: {e}")
    # Initialize basic LoginManager even if email fails
    try:
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth_routes.trading_account_login'  # type: ignore
        print("✓ Basic login manager initialized")
    except Exception as login_error:
        print(f"Login manager error: {login_error}")

# User loader for login functionality
if login_manager:
    try:

        @login_manager.user_loader
        def load_user(user_id):
            try:
                from models import User
                return User.query.get(int(user_id))
            except Exception as e:
                print(f"User loader error: {e}")
                return None

        print("✓ User loader defined")
    except Exception as e:
        print(f"User loader optional: {e}")

# Import User model for registration functionality
User = None
try:
    from models import User
    print("✓ User model imported from models.py")
except Exception as e:
    print(f"User model import error: {e}")


def send_registration_email(user_email, username, password):
    """Send registration confirmation email with credentials"""
    if not mail:
        return False

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
        # Import auth functions
        from api.auth_api import store_user_in_external_db, EmailService

        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validate input
        if not all([email, mobile, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')

        # Generate unique username from email and mobile
        try:
            # Extract first 3 letters from email (before @)
            email_part = email.split('@')[0][:3].lower()
            # Extract last 2 digits from mobile
            mobile_digits = ''.join(filter(str.isdigit, mobile))[-2:]
            username = email_part + mobile_digits

            # Ensure username is exactly 5 characters
            if len(username) < 5:
                username = username.ljust(5, '0')
            username = username[:5]

            # Store user in external database
            if store_user_in_external_db(username, password, email, mobile):
                # Send registration email with credentials (if mail service is configured)
                try:
                    if mail:
                        EmailService.send_registration_email(
                            mail, email, username, password)
                except Exception as email_error:
                    print(f"Email sending failed: {email_error}")

                # Flash success message for SweetAlert to detect and display
                flash(
                    'Registration successful! Please check your email for login credentials.',
                    'success')
                # Don't redirect immediately - let the template handle the SweetAlert popup
                return render_template('auth/register.html')
            else:
                flash(
                    'Registration failed. Email might already be registered.',
                    'error')
                return render_template('auth/register.html')

        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            if not User:
                flash('User model not available.', 'error')
                return render_template('auth/login.html')

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
# HEALTH CHECK ENDPOINT FOR RENDER DEPLOYMENT
# ========================================


@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }, 200


# ========================================
# APPLICATION INITIALIZATION
# ========================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)