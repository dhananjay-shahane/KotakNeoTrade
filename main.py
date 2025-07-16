
"""
Unified Kotak Neo Trading Platform
Main application that handles all routes and dynamic content loading
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, jsonify, request, flash
from flask_sqlalchemy import SQLAlchemy

# Add kotak_neo_project to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'kotak_neo_project'))

# Import all the necessary modules from kotak_neo_project
from Scripts.trading_functions import TradingFunctions
from Scripts.neo_client import NeoClient
from core.auth import require_auth, validate_current_session
from core.database import get_db_connection

# Initialize Flask app
app = Flask(__name__, 
           template_folder='kotak_neo_project/templates',
           static_folder='kotak_neo_project/static',
           static_url_path='/kotak/static')

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kotak_neo_project/instance/trading_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
trading_functions = TradingFunctions()
neo_client = NeoClient()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Root route - redirect to dashboard if authenticated, else login"""
    if session.get('authenticated'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Handle login logic here
        data = request.get_json() if request.is_json else request.form
        
        try:
            # Use your existing neo_client login logic
            login_result = neo_client.login(
                user_id=data.get('user_id'),
                password=data.get('password'),
                neo_fin_key=data.get('neo_fin_key'),
                consumer_key=data.get('consumer_key'),
                consumer_secret=data.get('consumer_secret')
            )
            
            if login_result and login_result.get('success'):
                session['authenticated'] = True
                session['client'] = login_result.get('client')
                session['ucc'] = data.get('user_id')
                session['login_time'] = datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')
                
                if request.is_json:
                    return jsonify({'success': True, 'redirect_url': url_for('dashboard')})
                return redirect(url_for('dashboard'))
            else:
                error_msg = login_result.get('message', 'Login failed')
                if request.is_json:
                    return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'error')
                
        except Exception as e:
            error_msg = f'Login error: {str(e)}'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            flash(error_msg, 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with all content loading capability"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('login'))

        # Get dashboard data
        dashboard_data = {}
        try:
            raw_dashboard_data = trading_functions.get_dashboard_data(client)
            
            if isinstance(raw_dashboard_data, dict):
                dashboard_data = raw_dashboard_data
            elif isinstance(raw_dashboard_data, list):
                dashboard_data = {
                    'positions': raw_dashboard_data,
                    'holdings': [],
                    'limits': {},
                    'recent_orders': []
                }
            else:
                dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': []
                }

            # Ensure all required keys exist
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])
            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))

        except Exception as e:
            logger.error(f"Dashboard data fetch failed: {e}")
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
        logger.error(f"Dashboard error: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', data={})

# API Routes for dynamic content loading
@app.route('/api/positions')
@login_required
def api_positions():
    """API endpoint for positions data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        positions_data = trading_functions.get_positions(client)
        
        if isinstance(positions_data, dict) and 'error' in positions_data:
            return jsonify({
                'success': False,
                'message': positions_data['error'],
                'positions': []
            }), 400

        if not isinstance(positions_data, list):
            positions_data = []

        # Calculate summary
        total_pnl = 0.0
        long_positions = 0
        short_positions = 0

        for position in positions_data:
            pnl = float(position.get('urPnl') or position.get('pnl') or 0)
            total_pnl += pnl
            
            buy_qty = float(position.get('flBuyQty') or position.get('buyQty') or 0)
            sell_qty = float(position.get('flSellQty') or position.get('sellQty') or 0)
            net_qty = buy_qty - sell_qty
            
            if net_qty > 0:
                long_positions += 1
            elif net_qty < 0:
                short_positions += 1

        return jsonify({
            'success': True,
            'positions': positions_data,
            'summary': {
                'total_pnl': total_pnl,
                'long_positions': long_positions,
                'short_positions': short_positions,
                'total_positions': len(positions_data)
            }
        })

    except Exception as e:
        logger.error(f"API positions error: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'positions': []
        }), 500

@app.route('/api/holdings')
@login_required
def api_holdings():
    """API endpoint for holdings data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        holdings_data = trading_functions.get_holdings(client)
        
        if isinstance(holdings_data, dict) and 'error' in holdings_data:
            return jsonify({
                'success': False,
                'message': holdings_data['error'],
                'holdings': []
            }), 400

        if not isinstance(holdings_data, list):
            holdings_data = []

        # Calculate summary
        total_invested = sum(float(h.get('holdingCost', 0) or 0) for h in holdings_data)
        current_value = sum(float(h.get('mktValue', 0) or 0) for h in holdings_data)

        return jsonify({
            'success': True,
            'holdings': holdings_data,
            'summary': {
                'total_holdings': len(holdings_data),
                'total_invested': total_invested,
                'current_value': current_value,
                'total_pnl': current_value - total_invested
            }
        })

    except Exception as e:
        logger.error(f"API holdings error: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'holdings': []
        }), 500

@app.route('/api/orders')
@login_required
def api_orders():
    """API endpoint for orders data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        orders_data = trading_functions.get_orders(client)
        
        if not isinstance(orders_data, list):
            orders_data = []

        return jsonify({
            'success': True,
            'orders': orders_data,
            'total_orders': len(orders_data)
        })

    except Exception as e:
        logger.error(f"API orders error: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'orders': []
        }), 500

@app.route('/api/etf-signals')
@login_required
def api_etf_signals():
    """API endpoint for ETF signals data"""
    try:
        from Scripts.external_db_service import get_etf_signals_from_external_db
        
        signals = get_etf_signals_from_external_db()
        if not signals:
            signals = []

        return jsonify({
            'success': True,
            'signals': signals,
            'total_signals': len(signals)
        })

    except Exception as e:
        logger.error(f"API ETF signals error: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'signals': []
        }), 500

@app.route('/api/deals')
@login_required
def api_deals():
    """API endpoint for deals data"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM user_deals 
                ORDER BY created_at DESC
            """)
            deals = cursor.fetchall()
            
            # Convert to list of dicts
            columns = [desc[0] for desc in cursor.description]
            deals_list = [dict(zip(columns, deal)) for deal in deals]

        conn.close()

        return jsonify({
            'success': True,
            'deals': deals_list,
            'total_deals': len(deals_list)
        })

    except Exception as e:
        logger.error(f"API deals error: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'deals': []
        }), 500

@app.route('/api/user_profile')
@login_required
def api_user_profile():
    """API endpoint for user profile"""
    try:
        profile_data = {
            'greeting_name': session.get('greeting_name', session.get('ucc', 'User')),
            'ucc': session.get('ucc', 'N/A'),
            'login_time': session.get('login_time', 'N/A'),
            'authenticated': session.get('authenticated', False),
            'client_code': session.get('client_code', 'N/A')
        }

        return jsonify({'success': True, 'profile': profile_data})

    except Exception as e:
        logger.error(f"User profile API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Content loading routes (for SPA-like behavior)
@app.route('/content/positions')
@login_required
def content_positions():
    """Return positions content HTML"""
    return render_template('positions.html')

@app.route('/content/holdings')
@login_required
def content_holdings():
    """Return holdings content HTML"""
    return render_template('holdings.html')

@app.route('/content/orders')
@login_required
def content_orders():
    """Return orders content HTML"""
    return render_template('orders.html')

@app.route('/content/charts')
@login_required
def content_charts():
    """Return charts content HTML"""
    return render_template('charts.html')

@app.route('/content/etf-signals')
@login_required
def content_etf_signals():
    """Return ETF signals content HTML"""
    return render_template('etf_signals.html')

@app.route('/content/deals')
@login_required
def content_deals():
    """Return deals content HTML"""
    return render_template('deals.html')

@app.route('/content/basic-signals')
@login_required
def content_basic_signals():
    """Return basic signals content HTML"""
    return render_template('basic_etf_signals.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
