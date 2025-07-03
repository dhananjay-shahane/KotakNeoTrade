"""
Kotak Neo Trading Platform - Main Flask Application
Provides a comprehensive trading interface with real-time market data,
portfolio management, and automated trading signals.
"""
import os
import sys
import logging
from dotenv import load_dotenv

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

from flask import Flask, request, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    """Base class for SQLAlchemy database models"""
    pass

# Initialize Flask application and database
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# ========================================
# APPLICATION CONFIGURATION
# ========================================

# Security configuration
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Enable HTTPS URL generation

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,     # Recycle connections every 5 minutes
    "pool_pre_ping": True,   # Verify connections before use
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
try:
    from Scripts.supabase_client import SupabaseClient
    supabase_client = SupabaseClient()
except Exception as e:
    print(f"Supabase client initialization failed: {e}")
    supabase_client = None

neo_client = NeoClient()
trading_functions = TradingFunctions()
user_manager = UserManager()
session_helper = SessionHelper()
websocket_handler = WebSocketHandler()

# Log Supabase connection status
try:
    if supabase_client and supabase_client.is_connected():
        logging.info("✅ Supabase integration active")
    else:
        logging.warning(
            "⚠️ Supabase not configured, using local database only")
except:
    logging.warning("⚠️ Supabase not configured, using local database only")


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
    """Login page with TOTP authentication only"""
    # Check if session expired and show message
    session_expired = request.args.get('expired') == 'true'
    if session_expired:
        flash('Your session has expired. Please login again.', 'warning')
    if request.method == 'POST':
        try:
            # Get form data
            mobile_number = request.form.get('mobile_number', '').strip()
            ucc = request.form.get('ucc', '').strip()
            totp = request.form.get('totp', '').strip()
            mpin = request.form.get('mpin', '').strip()

            # Validate inputs
            if not all([mobile_number, ucc, totp, mpin]):
                flash('All fields are required', 'error')
                return render_template('login.html')

            # Validate formats
            if len(mobile_number) != 10 or not mobile_number.isdigit():
                flash('Mobile number must be 10 digits', 'error')
                return render_template('login.html')

            if len(totp) != 6 or not totp.isdigit():
                flash('TOTP must be 6 digits', 'error')
                return render_template('login.html')

            if len(mpin) != 6 or not mpin.isdigit():
                flash('MPIN must be 6 digits', 'error')
                return render_template('login.html')

            # Execute TOTP login
            result = neo_client.execute_totp_login(mobile_number, ucc, totp,
                                                   mpin)

            if result and result.get('success'):
                client = result.get('client')
                session_data = result.get('session_data', {})

                # Store in session
                session['authenticated'] = True
                session['access_token'] = session_data.get('access_token')
                session['session_token'] = session_data.get('session_token')
                session['sid'] = session_data.get('sid')
                session['ucc'] = ucc
                session['client'] = client
                session['login_time'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                session['greeting_name'] = session_data.get(
                    'greetingName', ucc)
                session.permanent = True

                # Set session expiration (24 hours from now)
                expiry_time = datetime.now() + timedelta(hours=24)
                session['session_expires_at'] = expiry_time.isoformat()

                # Store additional user data
                session['rid'] = session_data.get('rid')
                session['user_id'] = session_data.get('user_id')
                session['client_code'] = session_data.get('client_code')
                session['is_trial_account'] = session_data.get(
                    'is_trial_account')

                # Store user data in database
                try:
                    login_response = {
                        'success': True,
                        'data': {
                            'ucc':
                            ucc,
                            'mobile_number':
                            mobile_number,
                            'greeting_name':
                            session_data.get('greetingName'),
                            'user_id':
                            session_data.get('user_id'),
                            'client_code':
                            session_data.get('client_code'),
                            'product_code':
                            session_data.get('product_code'),
                            'account_type':
                            session_data.get('account_type'),
                            'branch_code':
                            session_data.get('branch_code'),
                            'is_trial_account':
                            session_data.get('is_trial_account', False),
                            'access_token':
                            session_data.get('access_token'),
                            'session_token':
                            session_data.get('session_token'),
                            'sid':
                            session_data.get('sid'),
                            'rid':
                            session_data.get('rid')
                        }
                    }

                    db_user = user_manager.create_or_update_user(
                        login_response)
                    user_session = user_manager.create_user_session(
                        db_user.id, login_response)

                    session['db_user_id'] = db_user.id
                    session['db_session_id'] = user_session.session_id

                    logging.info(
                        f"User data stored in database for UCC: {ucc}")

                except Exception as db_error:
                    logging.error(
                        f"Failed to store user data in database: {db_error}")

                flash('Successfully authenticated with TOTP!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error_msg = result.get(
                    'message',
                    'Authentication failed') if result else 'Login failed'
                flash(f'TOTP login failed: {error_msg}', 'error')

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with portfolio overview"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch dashboard data with error handling
        dashboard_data = {}
        try:
            raw_dashboard_data = trading_functions.get_dashboard_data(client)

            # Ensure dashboard_data is always a dictionary
            if isinstance(raw_dashboard_data, dict):
                dashboard_data = raw_dashboard_data
                # Validate that positions and holdings are lists
                if not isinstance(dashboard_data.get('positions'), list):
                    dashboard_data['positions'] = []
                if not isinstance(dashboard_data.get('holdings'), list):
                    dashboard_data['holdings'] = []
                if not isinstance(dashboard_data.get('limits'), dict):
                    dashboard_data['limits'] = {}
                if not isinstance(dashboard_data.get('recent_orders'), list):
                    dashboard_data['recent_orders'] = []
            elif isinstance(raw_dashboard_data, list):
                # If API returns a list directly, wrap it properly
                dashboard_data = {
                    'positions': raw_dashboard_data,
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': len(raw_dashboard_data),
                    'total_holdings': 0,
                    'total_orders': 0
                }
            else:
                # Fallback empty structure
                dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': 0,
                    'total_holdings': 0,
                    'total_orders': 0
                }

            # Ensure all required keys exist with default values
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])
            dashboard_data.setdefault('total_positions',
                                      len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings',
                                      len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders',
                                      len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            # For errors, show dashboard with empty data
            flash(f'Some data could not be loaded: {str(dashboard_error)}',
                  'warning')
            dashboard_data = {
                'positions': [],
                'holdings': [],
                'limits': {},
                'recent_orders': [],
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0
            }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        # Return dashboard with empty data structure
        empty_data = {
            'positions': [],
            'holdings': [],
            'limits': {},
            'recent_orders': [],
            'total_positions': 0,
            'total_holdings': 0,
            'total_orders': 0
        }
        return render_template('dashboard.html', data=empty_data)


@app.route('/positions')
@require_auth
def positions():
    """Positions page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch positions data
        positions_data = trading_functions.get_positions(client)

        # Ensure positions_data is a list
        if isinstance(positions_data, dict):
            if 'data' in positions_data:
                positions_list = positions_data['data']
            elif 'positions' in positions_data:
                positions_list = positions_data['positions']
            else:
                positions_list = []
        elif isinstance(positions_data, list):
            positions_list = positions_data
        else:
            positions_list = []

        return render_template('positions.html', positions=positions_list)

    except Exception as e:
        logging.error(f"Positions page error: {e}")
        flash(f'Error loading positions: {str(e)}', 'error')
        return render_template('positions.html', positions=[])


@app.route('/holdings')
@require_auth
def holdings():
    """Holdings page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch holdings data
        holdings_data = trading_functions.get_holdings(client)

        # Ensure holdings_data is a list
        if isinstance(holdings_data, dict):
            if 'data' in holdings_data:
                holdings_list = holdings_data['data']
            elif 'holdings' in holdings_data:
                holdings_list = holdings_data['holdings']
            else:
                holdings_list = []
        elif isinstance(holdings_data, list):
            holdings_list = holdings_data
        else:
            holdings_list = []

        return render_template('holdings.html', holdings=holdings_list)

    except Exception as e:
        logging.error(f"Holdings page error: {e}")
        flash(f'Error loading holdings: {str(e)}', 'error')
        return render_template('holdings.html', holdings=[])


@app.route('/orders')
@require_auth
def orders():
    """Orders page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Fetch orders data
        orders_data = trading_functions.get_orders(client)

        # Ensure orders_data is a list
        if isinstance(orders_data, dict):
            if 'data' in orders_data:
                orders_list = orders_data['data']
            elif 'orders' in orders_data:
                orders_list = orders_data['orders']
            else:
                orders_list = []
        elif isinstance(orders_data, list):
            orders_list = orders_data
        else:
            orders_list = []

        return render_template('orders.html', orders=orders_list)

    except Exception as e:
        logging.error(f"Orders page error: {e}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders.html', orders=[])


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


@app.route('/supabase-admin')
@require_auth
def supabase_admin():
    """Supabase Integration Admin Dashboard"""
    return render_template('supabase_admin.html')


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
    """API endpoint to get default deals data directly from admin_trade_signals with correct column mapping"""
    try:
        import logging
        logging.info(
            "Default deals API: Fetching data from admin_trade_signals table")

        # Connect to external database using the same connection as ETF signals
        connection_string = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"

        import psycopg2
        from psycopg2.extras import RealDictCursor

        # Connect to external database
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                query = """
                    SELECT id, etf, symbol, thirty, dh, date, pos, qty, ep, cmp, chan, inv, 
                           tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at
                    FROM admin_trade_signals 
                    WHERE symbol IS NOT NULL
                    ORDER BY created_at DESC, id DESC
                """

                cursor.execute(query)
                signals = cursor.fetchall()

                # Format signals as default deals data for frontend
                deals_data = []
                total_investment = 0
                total_current_value = 0
                total_pnl = 0
                count = 0

                for row in signals:
                    count += 1
                    # Calculate values with proper null handling using CSV column names
                    entry_price = float(
                        row.get('ep')
                        or 0) if row.get('ep') is not None else 0.0
                    current_price = float(
                        row.get('cmp')
                        or 0) if row.get('cmp') is not None else 0.0
                    quantity = int(row.get('qty')
                                   or 0) if row.get('qty') is not None else 0
                    investment = float(
                        row.get('inv')
                        or 0) if row.get('inv') is not None else 0.0
                    pnl_amount = float(row.get('pl') or
                                       0) if row.get('pl') is not None else 0.0
                    target_price = float(
                        row.get('tp')
                        or 0) if row.get('tp') is not None else 0.0
                    current_value = float(
                        row.get('tva')
                        or 0) if row.get('tva') is not None else 0.0

                    # Handle percentage change
                    chan_value = row.get('chan') or '0'
                    if isinstance(chan_value, str):
                        chan_value = chan_value.replace('%', '')
                    pnl_pct = float(chan_value) if chan_value else 0.0

                    # Position type from pos column (1 = BUY, -1 = SELL)
                    pos = int(row.get('pos', 1))
                    position_type = 'BUY' if pos > 0 else 'SELL'

                    # Accumulate totals
                    total_investment += investment
                    total_current_value += current_value
                    total_pnl += pnl_amount

                    deal_dict = {
                        'trade_signal_id': row.get('id') or count,
                        'id': row.get('id') or count,
                        'etf': row.get('etf') or 'N/A',
                        'symbol': row.get('symbol') or 'N/A',
                        'thirty': row.get('thirty') or '',
                        'dh': row.get('dh') or '',
                        'date': str(row.get('date') or ''),
                        'pos': pos,
                        'position_type': position_type,
                        'qty': quantity,
                        'ep': entry_price,
                        'cmp': current_price,
                        'chan': row.get('chan') or f'{pnl_pct:.2f}%',
                        'inv': investment,
                        'tp': target_price,
                        'tva': current_value,
                        'tpr': row.get('tpr') or '',
                        'pl': pnl_amount,
                        'ed': row.get('ed') or '',
                        'exp': row.get('exp') or '',
                        'pr': row.get('pr') or '',
                        'pp': row.get('pp') or '',
                        'iv': row.get('iv') or '',
                        'ip': row.get('ip') or '',
                        'nt': row.get('nt') or 0,
                        'qt': float(row.get('qt') or 0),
                        'seven': row.get('seven') or '',
                        'ch': row.get('ch') or '',
                        'created_at': str(row.get('created_at') or ''),
                        # Standard fields for compatibility
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'quantity': quantity,
                        'investment_amount': investment,
                        'target_price': target_price,
                        'total_value': current_value,
                        'pnl': pnl_amount,
                        'price_change_percent': pnl_pct,
                        'entry_date': str(row.get('date') or ''),
                        'admin_signal_id': row.get('id'),
                        'status': 'ACTIVE'
                    }
                    deals_data.append(deal_dict)

        logging.info(
            f"Default deals API: Returning {len(deals_data)} deals from admin_trade_signals"
        )

        return jsonify({
            'success': True,
            'data': deals_data,
            'total_count': len(deals_data),
            'portfolio': {
                'total_investment': total_investment,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'total_positions': len(deals_data)
            }
        })

    except Exception as e:
        logging.error(f"Error fetching default deals data: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'data': []}), 500


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


@app.route('/api/test-auto-sync', methods=['POST'])
def test_auto_sync_endpoint():
    """API endpoint to test automatic synchronization"""
    try:
        from Scripts.auto_sync_system import test_auto_sync
        test_result = test_auto_sync()

        return jsonify({
            'success':
            test_result,
            'message':
            'Auto-sync test passed' if test_result else 'Auto-sync test failed'
        })

    except Exception as e:
        logging.error(f"Error testing auto-sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/place-order', methods=['POST'])
@require_auth  
def place_order():
    """API endpoint to place buy/sell orders using Kotak Neo API"""
    try:
        from Scripts.trading_functions import TradingFunctions

        # Get order data from request
        order_data = request.get_json()

        # Validate required fields
        required_fields = [
            'symbol', 'quantity', 'transaction_type', 'order_type'
        ]
        for field in required_fields:
            if field not in order_data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400

        # Get client from session
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        # Validate session before placing order
        try:
            # Quick session validation by checking if we can fetch basic data
            from Scripts.neo_client import NeoClient
            neo_client = NeoClient()
            if not neo_client.validate_session(client):
                return jsonify({
                    'success':
                    False,
                    'message':
                    'Trading session has expired. Please logout and login again to enable trading operations.'
                }), 401
        except Exception as e:
            logging.warning(f"Session validation failed: {e}")
            # Continue with order placement attempt

        # Initialize trading functions
        trading_functions = TradingFunctions()

        # Prepare order data with defaults
        order_params = {
            'symbol': order_data['symbol'],
            'quantity': str(order_data['quantity']),
            'transaction_type':
            order_data['transaction_type'],  # B (Buy) or S (Sell)
            'order_type': order_data['order_type'],  # MARKET, LIMIT, STOPLOSS
            'exchange_segment': order_data.get('exchange_segment', 'nse_cm'),
            'product': order_data.get('product', 'CNC'),  # CNC, MIS, NRML
            'validity': order_data.get('validity', 'DAY'),
            'price': order_data.get('price', '0'),
            'trigger_price': order_data.get('trigger_price', '0'),
            'disclosed_quantity': order_data.get('disclosed_quantity', '0'),
            'amo': order_data.get('amo', 'NO'),
            'market_protection': order_data.get('market_protection', '0'),
            'pf': order_data.get('pf', 'N'),
            'tag': order_data.get('tag', None)
        }

        # Place the order
        result = trading_functions.place_order(client, order_params)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message':
                f'Order placed successfully for {order_data["symbol"]}',
                'data': result.get('data'),
                'order_id': result.get('order_id')
            })
        else:
            error_message = result.get('message', 'Failed to place order')

            # Check for specific API authentication errors
            if 'invalid access type' in error_message.lower(
            ) or 'not_ok' in str(result).lower():
                error_message = 'Trading session has expired. Please logout and login again to place orders.'
            elif 'session' in error_message.lower():
                error_message = 'Session expired. Please refresh the page and try again.'

            return jsonify({'success': False, 'message': error_message}), 400

    except Exception as e:
        logging.error(f"Error placing order: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


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


# Google Finance Scheduler API endpoints
@app.route('/api/google-finance-scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get Google Finance scheduler status"""
    try:
        from Scripts.google_finance_scheduler import get_scheduler_status
        return jsonify(get_scheduler_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/google-finance-scheduler/start', methods=['POST'])
def start_scheduler():
    """Start Google Finance scheduler"""
    try:
        from Scripts.google_finance_scheduler import start_google_finance_scheduler
        start_google_finance_scheduler()
        return jsonify({'success': True, 'message': 'Google Finance scheduler started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/google-finance-scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop Google Finance scheduler"""
    try:
        from Scripts.google_finance_scheduler import stop_google_finance_scheduler
        stop_google_finance_scheduler()
        return jsonify({'success': True, 'message': 'Google Finance scheduler stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/google-finance-scheduler/force-update', methods=['POST'])
def force_scheduler_update():
    """Force an immediate Google Finance update"""
    try:
        from Scripts.google_finance_scheduler import force_update_now
        result = force_update_now()
        if result:
            return jsonify({'success': True, 'message': 'Update triggered successfully'})
        else:
            return jsonify({'success': False, 'message': 'Scheduler not running'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    from api.supabase_api import supabase_bp
    from api.deals import deals_bp  # Added deals blueprint import
    from api.google_finance_api import google_finance_bp
    from api.yahoo_finance_api import yahoo_bp  #Import yahoo blueprint

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
    app.register_blueprint(
        deals_bp,
        url_prefix='/api/deals')  # Register deals blueprint with prefix
    print("✓ Deals blueprint registered")
except Exception as e:
    print(f"Warning: Could not register deals blueprint: {e}")

# Register ETF signals blueprint
    app.register_blueprint(etf_bp, url_prefix='/api')
    
    # Register other blueprints
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(quotes_bp, url_prefix='/api')
    app.register_blueprint(datatable_bp, url_prefix='/api')
    app.register_blueprint(enhanced_etf_bp, url_prefix='/api')
    app.register_blueprint(admin_signals_bp, url_prefix='/api')
    app.register_blueprint(supabase_bp, url_prefix='/api')
    
    # Register Google Finance API blueprint
    try:
        from api.google_finance_api import google_finance_bp
        app.register_blueprint(google_finance_bp)
        logging.info("✓ Google Finance API blueprint registered")
    except ImportError as e:
        logging.warning(f"Could not register Google Finance API: {e}")

    # Register Performance Calculator API blueprint
    try:
        from api.performance_calculator import performance_bp
        app.register_blueprint(performance_bp)
        logging.info("✓ Performance Calculator API blueprint registered")
    except ImportError as e:
        logging.warning(f"Could not register Performance Calculator API: {e}")

    # Register Yahoo Finance API blueprint
    app.register_blueprint(yahoo_bp)

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


# Live CMP update endpoint using Google Finance
@app.route('/api/google-finance/update-etf-cmp', methods=['GET', 'POST'])
def update_live_cmp_endpoint():
    """API endpoint to update live CMP data using Google Finance via yfinance"""
    try:
        from Scripts.google_finance_cmp_updater import update_all_cmp_data

        result = update_all_cmp_data()

        return jsonify({
            'success':
            result['success'],
            'message':
            result['message'],
            'updated_count':
            result['updated_count'],
            'total_symbols':
            result.get('total_symbols', 0),
            'successful_symbols':
            result.get('successful_symbols', 0),
            'error_count':
            result['error_count'],
            'duration':
            result.get('duration', 0),
            'results':
            result.get('results', {})
        })

    except Exception as e:
        import logging
        logging.error(f"Error updating live CMP via Google Finance: {str(e)}")
        return jsonify({
            'success':
            False,
            'error':
            str(e),
            'message':
            'Failed to update live CMP data via Google Finance'
        }), 500


# Update specific symbols CMP endpoint
@app.route('/api/update-cmp-symbols', methods=['POST'])
def update_specific_symbols_cmp():
    """API endpoint to update CMP for specific symbols"""
    try:
        from Scripts.google_finance_cmp_updater import update_specific_cmp_data
        from flask import request

        data = request.get_json()
        symbols = data.get('symbols', []) if data else []

        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols provided'
            }), 400

        result = update_specific_cmp_data(symbols)

        return jsonify({
            'success':
            result['success'],
            'message':
            result['message'],
            'updated_count':
            result['updated_count'],
            'symbols_processed':
            result.get('symbols_processed', 0),
            'successful_symbols':
            result.get('successful_symbols', 0),
            'error_count':
            result['error_count'],
            'duration':
            result.get('duration', 0),
            'results':
            result.get('results', {})
        })

    except Exception as e:
        import logging
        logging.error(f"Error updating specific symbols CMP: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update specific symbols CMP'
        }), 500


@app.route('/api/update-comprehensive-calculations', methods=['POST'])
def update_comprehensive_calculations():
    """API endpoint to update comprehensive trading calculations for all symbols"""
    try:
        from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
        
        updater = GoogleFinanceCMPUpdater()
        result = updater.update_all_symbols()
        
        return jsonify({
            'success': True,
            'message': 'Comprehensive calculations updated successfully',
            'data': {
                'updated_symbols': result.get('updated_symbols', 0),
                'total_updated_rows': result.get('total_updated_rows', 0),
                'calculation_summary': result.get('calculation_summary', {}),
                'processing_time': result.get('processing_time', 0)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating comprehensive calculations: {str(e)}'
        }), 500


@app.route('/api/calculate-symbol-metrics/<symbol>', methods=['GET'])
def calculate_symbol_metrics(symbol):
    """API endpoint to calculate metrics for a specific symbol"""
    try:
        from Scripts.trading_calculations import TradingCalculations
        
        db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
        
        calculator = TradingCalculations(db_config)
        
        # Get trade data for the symbol
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_trade_signals 
                    WHERE (symbol = %s OR etf = %s)
                    AND qty IS NOT NULL AND ep IS NOT NULL
                    LIMIT 1
                """, (symbol, symbol))
                
                trade = cursor.fetchone()
                
                if trade:
                    trade_dict = dict(trade)
                    calculated_metrics = calculator.calculate_all_metrics(trade_dict)
                    
                    return jsonify({
                        'success': True,
                        'symbol': symbol,
                        'trade_data': trade_dict,
                        'calculated_metrics': calculated_metrics
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'No trade data found for symbol {symbol}'
                    }), 404
                    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error calculating metrics for {symbol}: {str(e)}'
        }), 500


# Health check endpoint for domain verification
@app.route('/health')
def health_check():
    """Health check endpoint for domain verification"""
    return {
        'status': 'ok',
        'message': 'Kotak Neo Trading Platform is running',
        'port': 5000
    }, 200


# Test endpoint for DNS verification
@app.route('/test')
def test_endpoint():
    """Test endpoint for DNS verification"""
    return {
        'message': 'DNS test successful',
        'domain': os.environ.get('REPLIT_DOMAINS', 'localhost')
    }, 200


# Simple HTML page for testing external access
@app.route('/preview')
def preview_test():
    """Simple preview test page"""
    correct_domain = os.environ.get('REPLIT_DOMAINS', 'localhost')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kotak Neo Trading Platform - Preview Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #28a745; font-size: 18px; font-weight: bold; }}
            .info {{ color: #007bff; margin: 10px 0; }}
            .error {{ color: #dc3545; margin: 10px 0; }}
            .correct-url {{ background: #e9ecef; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="success">✓ Preview Access Working!</h1>
            <p class="info">Kotak Neo Trading Platform is running successfully</p>

            <div class="correct-url">
                <strong>Correct URL:</strong><br>
                <a href="https://{correct_domain}/" target="_blank">https://{correct_domain}/</a>
            </div>

            <p class="error">⚠️ DNS Issues? Try these solutions:</p>
            <ol>
                <li>Use Replit's built-in webview (click the preview/webview button in Replit)</li>
                <li>Wait 2-3 minutes for domain propagation</li>
                <li>Clear your browser cache and try again</li>
                <li>Try accessing from an incognito/private browser window</li>
            </ol>

            <p>Status: Application is accessible from external domains</p>
            <a href="/">Go to Login Page</a>
        </div>
    </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)