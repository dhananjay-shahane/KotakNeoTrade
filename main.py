import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup library paths for pandas/numpy dependencies
def setup_library_paths():
    """Setup LD_LIBRARY_PATH for required libraries"""
    os.environ['LD_LIBRARY_PATH'] = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    print(f"Set LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")

# Setup environment before importing Flask modules
setup_library_paths()

from app import app  # noqa: F401

# Register blueprints only once to avoid conflicts
try:
    from routes.auth import auth_bp
    from routes.main import main_bp
    from api.dashboard import dashboard_api as dashboard_bp
    from api.trading import trading_api as trading_bp
    # Import etf_bp after app initialization to avoid circular imports
    from api.admin import admin_bp
    from api.deals import deals_bp
    from api.notifications import notifications_bp
    from api.supabase_api import supabase_bp
    from api.admin_signals_api import admin_signals_bp
    from api.signals_datatable import datatable_bp as signals_datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp

    # Import realtime quotes after creating the manager
    from api.realtime_quotes import quotes_bp as realtime_bp

    # Check if blueprints are already registered to avoid duplicates
    registered_blueprints = [bp.name for bp in app.blueprints.values()]

    if 'auth' not in registered_blueprints:
        app.register_blueprint(auth_bp)
    if 'main' not in registered_blueprints:
        app.register_blueprint(main_bp)
    if 'dashboard_api' not in registered_blueprints:
        app.register_blueprint(dashboard_bp)
    if 'trading_api' not in registered_blueprints:
        app.register_blueprint(trading_bp)
    # Register ETF blueprint
    try:
        import sys
        import importlib

        # Force reload the ETF signals module to ensure clean import
        if 'api.etf_signals' in sys.modules:
            importlib.reload(sys.modules['api.etf_signals'])

        from api.etf_signals import etf_bp

        # Remove any existing ETF blueprint registration
        if 'etf' in app.blueprints:
            del app.blueprints['etf']

        app.register_blueprint(etf_bp)
        print("✓ ETF signals blueprint registered successfully")

        # Verify the /etf/signals route exists
        etf_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/etf/')]
        if etf_routes:
            print(f"✓ ETF routes registered: {etf_routes}")
        else:
            print("✗ No ETF routes found after registration")

    except Exception as etf_error:
        print(f"✗ ETF blueprint registration failed: {etf_error}")
        import traceback
        traceback.print_exc()
    # Register additional blueprints only if not already registered
    if 'admin' not in registered_blueprints:
        app.register_blueprint(admin_bp)
    if 'quotes' not in registered_blueprints:
        app.register_blueprint(realtime_bp)
    if 'deals' not in registered_blueprints:
        app.register_blueprint(deals_bp)
    if 'notifications' not in registered_blueprints:
        app.register_blueprint(notifications_bp)
    if 'supabase' not in registered_blueprints:
        app.register_blueprint(supabase_bp)
    if 'admin_signals' not in registered_blueprints:
        app.register_blueprint(admin_signals_bp)
    if 'signals_datatable' not in registered_blueprints:
        app.register_blueprint(signals_datatable_bp)
    if 'enhanced_etf' not in registered_blueprints:
        app.register_blueprint(enhanced_etf_bp)

    print("✓ Additional blueprints registered successfully")
except Exception as e:
    print(f"✗ Error registering blueprints: {e}")
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    try:
        print("🚀 Starting Flask application...")

        # Start real-time quotes scheduler
        try:
            from realtime_quotes_manager import realtime_quotes_manager
            realtime_quotes_manager.start()
            print("📊 Real-time quotes scheduler started")
        except ImportError:
            print("⚠️  Real-time quotes manager not available, skipping")

        # Start Yahoo Finance scheduler
        from yahoo_scheduler import start_yahoo_scheduler
        start_yahoo_scheduler()
        print("📈 Yahoo Finance scheduler started")

        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))

        print(f"🌐 Application will be available at:")
        print(f"   Local: http://0.0.0.0:{port}")
        if os.environ.get('REPLIT_DOMAINS'):
            print(f"   External: https://{os.environ.get('REPLIT_DOMAINS')}")

        # Run with proper Replit configuration
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()

```

```python
from flask import Flask, request, jsonify
import logging
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_session import Session
import redis
import os
from datetime import datetime, timedelta
import pytz
import secrets  # Import the secrets module
from functools import wraps
from urllib.parse import urlparse, urljoin
import time

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app initialization
app = Flask(__name__)
app.debug = True  # Enable debug mode for development

# CORS Configuration
CORS(app, origins="*", supports_credentials=True)  # Allow all origins, adjust as needed for production
app.config['CORS_HEADERS'] = 'Content-Type'

# Secret key generation
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    secret_key = secrets.token_hex(32)
    logging.warning("SECRET_KEY not found in environment variables. Generating a random key. This is NOT suitable for production.")

app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)

# Session setup
server_session = Session(app)

# SocketIO setup
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# Rate limiting configuration
RATE_LIMIT = 200  # Number of requests allowed
RATE_LIMIT_WINDOW = 60  # Time window in seconds (e.g., 60 seconds = 1 minute)
api_usage = {}  # Dictionary to track API usage per IP address

# Custom error handlers
@app.errorhandler(404)
def not_found(error):
    logging.error(f"Not found error: {error}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    logging.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Security functions
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if target and is_safe_url(target):
            return target

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == os.environ.get('BASIC_AUTH_USERNAME') and auth.password == os.environ.get('BASIC_AUTH_PASSWORD')):
            logging.warning(f"Authentication failed for user: {auth.username if auth else 'None'}")
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        now = time.time()

        if client_ip not in api_usage:
            api_usage[client_ip] = []

        # Clean up old timestamps
        api_usage[client_ip] = [timestamp for timestamp in api_usage[client_ip] if now - timestamp < RATE_LIMIT_WINDOW]

        if len(api_usage[client_ip]) >= RATE_LIMIT:
            logging.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

        api_usage[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def convert_to_est(utc_dt):
    """Convert a UTC datetime object to EST."""
    utc_timezone = pytz.utc
    est_timezone = pytz.timezone('US/Eastern')
    utc_dt = utc_timezone.localize(utc_dt)
    est_dt = utc_dt.astimezone(est_timezone)
    return est_dt

def get_authenticated_client():
    """Get an authenticated trading client."""
    from trading_client import TradingClient  # Import inside function to avoid circular dependency
    try:
        API_KEY = os.environ.get('API_KEY')
        API_SECRET = os.environ.get('API_SECRET')
        trading_client = TradingClient(api_key=API_KEY, api_secret=API_SECRET, paper=True)
        return trading_client
    except Exception as e:
        logging.error(f"Error authenticating client: {str(e)}")
        return None

# WebSocket event handlers
@socketio.on('connect')
def test_connect():
    client_ip = request.remote_addr
    logging.info(f"Client connected: {client_ip}")
    socketio.emit('my response', {'data': 'Connected!'})

@socketio.on('disconnect')
def test_disconnect():
    client_ip = request.remote_addr
    logging.info(f"Client disconnected: {client_ip}")
    print('Client disconnected')

# API endpoints
@app.route('/api/hello', methods=['GET'])
def hello_world():
    logging.info("Hello world API was accessed")
    return jsonify({'message': 'Hello, World!'})

@app.route('/api/time', methods=['GET'])
def get_time():
    now_utc = datetime.utcnow()
    est_time = convert_to_est(now_utc).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    logging.info(f"Current time in EST: {est_time}")
    return jsonify({'time': est_time})

@app.route('/api/env', methods=['GET'])
def get_environment_variables():
    logging.info("Environment variables API was accessed")
    return jsonify({key: value for key, value in os.environ.items()})

@app.route('/api/quote', methods=['GET'])
def get_quote():
    symbol = request.args.get('symbol', 'AAPL')
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        quote = client.get_quote(symbol)
        logging.info(f"Quote for {symbol}: {quote}")
        return jsonify(quote)
    except Exception as e:
        logging.error(f"Error fetching quote for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        account = client.get_account()
        logging.info(f"Account details: {account}")
        return jsonify(account)
    except Exception as e:
        logging.error(f"Error fetching account details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        positions = client.get_positions()
        logging.info(f"Positions: {positions}")
        return jsonify(positions)
    except Exception as e:
        logging.error(f"Error fetching positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        orders = client.get_orders()
        logging.info(f"Orders: {orders}")
        return jsonify(orders)
    except Exception as e:
        logging.error(f"Error fetching orders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        qty = data.get('qty')
        side = data.get('side')
        type = data.get('type', 'market')  # Default to market if not specified
        time_in_force = data.get('time_in_force', 'gtc')  # Default to gtc if not specified
        
        if not all([symbol, qty, side]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})

        client = get_authenticated_client()
        if not client:
            return jsonify({'success': False, 'message': 'Authentication required'})

        order = client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force
        )

        logging.info(f"Order submitted: {order}")
        return jsonify({
            'success': True,
            'message': 'Order submitted successfully',
            'order': order
        })

    except Exception as e:
        logging.error(f"Error submitting order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    try:
        data = request.get_json()
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID is required'})

        # Get authenticated client
        client = get_authenticated_client()
        if not client:
            return jsonify({'success': False, 'message': 'Authentication required'})

        # Cancel the order using Neo client's cancel_order method
        response = client.cancel_order(order_id=order_id)

        if response and response.get('stat') == 'Ok':
            return jsonify({
                'success': True, 
                'message': 'Order cancelled successfully',
                'data': response
            })
        else:
            error_msg = response.get('emsg', 'Failed to cancel order') if response else 'No response from server'
            return jsonify({'success': False, 'message': error_msg})

    except Exception as e:
        logging.error(f"Error cancelling order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
```

```python
from flask import Flask, request, jsonify
import logging
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_session import Session
import redis
import os
from datetime import datetime, timedelta
import pytz
import secrets  # Import the secrets module
from functools import wraps
from urllib.parse import urlparse, urljoin
import time

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app initialization
app = Flask(__name__)
app.debug = True  # Enable debug mode for development

# CORS Configuration
CORS(app, origins="*", supports_credentials=True)  # Allow all origins, adjust as needed for production
app.config['CORS_HEADERS'] = 'Content-Type'

# Secret key generation
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    secret_key = secrets.token_hex(32)
    logging.warning("SECRET_KEY not found in environment variables. Generating a random key. This is NOT suitable for production.")

app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)

# Session setup
server_session = Session(app)

# SocketIO setup
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# Rate limiting configuration
RATE_LIMIT = 200  # Number of requests allowed
RATE_LIMIT_WINDOW = 60  # Time window in seconds (e.g., 60 seconds = 1 minute)
api_usage = {}  # Dictionary to track API usage per IP address

# Custom error handlers
@app.errorhandler(404)
def not_found(error):
    logging.error(f"Not found error: {error}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    logging.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Security functions
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if target and is_safe_url(target):
            return target

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == os.environ.get('BASIC_AUTH_USERNAME') and auth.password == os.environ.get('BASIC_AUTH_PASSWORD')):
            logging.warning(f"Authentication failed for user: {auth.username if auth else 'None'}")
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        now = time.time()

        if client_ip not in api_usage:
            api_usage[client_ip] = []

        # Clean up old timestamps
        api_usage[client_ip] = [timestamp for timestamp in api_usage[client_ip] if now - timestamp < RATE_LIMIT_WINDOW]

        if len(api_usage[client_ip]) >= RATE_LIMIT:
            logging.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

        api_usage[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def convert_to_est(utc_dt):
    """Convert a UTC datetime object to EST."""
    utc_timezone = pytz.utc
    est_timezone = pytz.timezone('US/Eastern')
    utc_dt = utc_timezone.localize(utc_dt)
    est_dt = utc_dt.astimezone(est_timezone)
    return est_dt

def get_authenticated_client():
    """Get an authenticated trading client."""
    from trading_client import TradingClient  # Import inside function to avoid circular dependency
    try:
        API_KEY = os.environ.get('API_KEY')
        API_SECRET = os.environ.get('API_SECRET')
        trading_client = TradingClient(api_key=API_KEY, api_secret=API_SECRET, paper=True)
        return trading_client
    except Exception as e:
        logging.error(f"Error authenticating client: {str(e)}")
        return None

# WebSocket event handlers
@socketio.on('connect')
def test_connect():
    client_ip = request.remote_addr
    logging.info(f"Client connected: {client_ip}")
    socketio.emit('my response', {'data': 'Connected!'})

@socketio.on('disconnect')
def test_disconnect():
    client_ip = request.remote_addr
    logging.info(f"Client disconnected: {client_ip}")
    print('Client disconnected')

# API endpoints
@app.route('/api/hello', methods=['GET'])
def hello_world():
    logging.info("Hello world API was accessed")
    return jsonify({'message': 'Hello, World!'})

@app.route('/api/time', methods=['GET'])
def get_time():
    now_utc = datetime.utcnow()
    est_time = convert_to_est(now_utc).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    logging.info(f"Current time in EST: {est_time}")
    return jsonify({'time': est_time})

@app.route('/api/env', methods=['GET'])
def get_environment_variables():
    logging.info("Environment variables API was accessed")
    return jsonify({key: value for key, value in os.environ.items()})

@app.route('/api/quote', methods=['GET'])
def get_quote():
    symbol = request.args.get('symbol', 'AAPL')
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        quote = client.get_quote(symbol)
        logging.info(f"Quote for {symbol}: {quote}")
        return jsonify(quote)
    except Exception as e:
        logging.error(f"Error fetching quote for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/account', methods=['GET'])
def get_account():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        account = client.get_account()
        logging.info(f"Account details: {account}")
        return jsonify(account)
    except Exception as e:
        logging.error(f"Error fetching account details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        positions = client.get_positions()
        logging.info(f"Positions: {positions}")
        return jsonify(positions)
    except Exception as e:
        logging.error(f"Error fetching positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    client = get_authenticated_client()
    if not client:
        return jsonify({'error': 'Authentication failed'}), 401
    try:
        orders = client.get_orders()
        logging.info(f"Orders: {orders}")
        return jsonify(orders)
    except Exception as e:
        logging.error(f"Error fetching orders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        qty = data.get('qty')
        side = data.get('side')
        type = data.get('type', 'market')  # Default to market if not specified
        time_in_force = data.get('time_in_force', 'gtc')  # Default to gtc if not specified
        
        if not all([symbol, qty, side]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})

        client = get_authenticated_client()
        if not client:
            return jsonify({'success': False, 'message': 'Authentication required'})

        order = client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force
        )

        logging.info(f"Order submitted: {order}")
        return jsonify({
            'success': True,
            'message': 'Order submitted successfully',
            'order': order
        })

    except Exception as e:
        logging.error(f"Error submitting order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/cancel_order', methods=['POST'])
def cancel_order():
    try:
        data = request.get_json()
        order_id = data.get('order_id')

        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID is required'})

        # Get authenticated client
        client = get_authenticated_client()
        if not client:
            return jsonify({'success': False, 'message': 'Authentication required'})

        # Cancel the order using Neo client's cancel_order method
        response = client.cancel_order(order_id=order_id)

        if response and response.get('stat') == 'Ok':
            return jsonify({
                'success': True, 
                'message': 'Order cancelled successfully',
                'data': response
            })
        else:
            error_msg = response.get('emsg', 'Failed to cancel order') if response else 'No response from server'
            return jsonify({'success': False, 'message': error_msg})

    except Exception as e:
        logging.error(f"Error cancelling order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
```

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup library paths for pandas/numpy dependencies
def setup_library_paths():
    """Setup LD_LIBRARY_PATH for required libraries"""
    os.environ['LD_LIBRARY_PATH'] = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    print(f"Set LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")

# Setup environment before importing Flask modules
setup_library_paths()

from app import app  # noqa: F401

# Register blueprints only once to avoid conflicts
try:
    from routes.auth import auth_bp
    from routes.main import main_bp
    from api.dashboard import dashboard_api as dashboard_bp
    from api.trading import trading_api as trading_bp
    # Import etf_bp after app initialization to avoid circular imports
    from api.admin import admin_bp
    from api.deals import deals_bp
    from api.notifications import notifications_bp
    from api.supabase_api import supabase_bp
    from api.admin_signals_api import admin_signals_bp
    from api.signals_datatable import datatable_bp as signals_datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp

    # Import realtime quotes after creating the manager
    from api.realtime_quotes import quotes_bp as realtime_bp

    # Check if blueprints are already registered to avoid duplicates
    registered_blueprints = [bp.name for bp in app.blueprints.values()]

    if 'auth' not in registered_blueprints:
        app.register_blueprint(auth_bp)
    if 'main' not in registered_blueprints:
        app.register_blueprint(main_bp)
    if 'dashboard_api' not in registered_blueprints:
        app.register_blueprint(dashboard_bp)
    if 'trading_api' not in registered_blueprints:
        app.register_blueprint(trading_bp)
    # Register ETF blueprint
    try:
        import sys
        import importlib

        # Force reload the ETF signals module to ensure clean import
        if 'api.etf_signals' in sys.modules:
            importlib.reload(sys.modules['api.etf_signals'])

        from api.etf_signals import etf_bp

        # Remove any existing ETF blueprint registration
        if 'etf' in app.blueprints:
            del app.blueprints['etf']

        app.register_blueprint(etf_bp)
        print("✓ ETF signals blueprint registered successfully")

        # Verify the /etf/signals route exists
        etf_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/etf/')]
        if etf_routes:
            print(f"✓ ETF routes registered: {etf_routes}")
        else:
            print("✗ No ETF routes found after registration")

    except Exception as etf_error:
        print(f"✗ ETF blueprint registration failed: {etf_error}")
        import traceback
        traceback.print_exc()
    # Register additional blueprints only if not already registered
    if 'admin' not in registered_blueprints:
        app.register_blueprint(admin_bp)
    if 'quotes' not in registered_blueprints:
        app.register_blueprint(realtime_bp)
    if 'deals' not in registered_blueprints:
        app.register_blueprint(deals_bp)
    if 'notifications' not in registered_blueprints:
        app.register_blueprint(notifications_bp)
    if 'supabase' not in registered_blueprints:
        app.register_blueprint(supabase_bp)
    if 'admin_signals' not in registered_blueprints:
        app.register_blueprint(admin_signals_bp)
    if 'signals_datatable' not in registered_blueprints:
        app.register_blueprint(signals_datatable_bp)
    if 'enhanced_etf' not in registered_blueprints:
        app.register_blueprint(enhanced_etf_bp)

    print("✓ Additional blueprints registered successfully")
except Exception as e:
    print(f"✗ Error registering blueprints: {e}")
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    try:
        print("🚀 Starting Flask application...")

        # Start real-time quotes scheduler
        try:
            from realtime_quotes_manager import realtime_quotes_manager
            realtime_quotes_manager.start()
            print("📊 Real-time quotes scheduler started")
        except ImportError:
            print("⚠️  Real-time quotes manager not available, skipping")

        # Start Yahoo Finance scheduler
        from yahoo_scheduler import start_yahoo_scheduler
        start_yahoo_scheduler()
        print("📈 Yahoo Finance scheduler started")

        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))

        print(f"🌐 Application will be available at:")
        print(f"   Local: http://0.0.0.0:{port}")
        if os.environ.get('REPLIT_DOMAINS'):
            print(f"   External: https://{os.environ.get('REPLIT_DOMAINS')}")

        # Run with proper Replit configuration
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()