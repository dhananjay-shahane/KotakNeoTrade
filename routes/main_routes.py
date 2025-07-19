"""
Main routes for Kotak Neo Trading Platform
Handles dashboard, positions, holdings, orders, and other main pages
"""
import logging
from flask import Blueprint, render_template, session, flash, redirect, url_for
from core.auth import require_auth, validate_current_session
from Scripts.trading_functions import TradingFunctions

# Create blueprint for main routes
main_bp = Blueprint('main_routes', __name__)

# Initialize trading functions
trading_functions = TradingFunctions()


@main_bp.route('/')
def index():
    """Root route - redirect to dashboard if authenticated, else login"""
    if validate_current_session():
        return redirect(url_for('main_routes.dashboard'))
    return redirect(url_for('auth_routes.trading_account_login'))


@main_bp.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with portfolio overview"""
    try:
        # For trading account login, client is not required
        if session.get('login_type') == 'trading_account':
            # Render dashboard with empty data for trading account users
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

        # For Kotak Neo login, require client
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth_routes.login'))

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
            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            flash(f'Some data could not be loaded: {str(dashboard_error)}', 'warning')
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


@main_bp.route('/positions')
@require_auth
def show_positions():
    """Display positions page"""
    logging.info(f"Request to show_positions")

    try:
        # Always show the positions page template - data will be loaded via AJAX
        return render_template('positions.html', page_title="Positions")

    except Exception as e:
        logging.error(f"Error in show_positions: {e}")
        return render_template('positions.html',
                             error=str(e),
                             page_title="Positions")


@main_bp.route('/holdings')
@require_auth
def show_holdings():
    """Show holdings page"""
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
    return render_template('holdings.html', kotak_account=kotak_account_data)


@main_bp.route('/orders')
@require_auth
def show_orders():
    """Display orders page"""
    logging.info(f"Request to show_orders")

    try:
        # Always show the orders page template - data will be loaded via AJAX
        return render_template('orders.html', page_title="Orders")

    except Exception as e:
        logging.error(f"Error in show_orders: {e}")
        return render_template('orders.html',
                             error=str(e),
                             page_title="Orders")


@main_bp.route('/charts')
@require_auth
def charts():
    """Charts page for trading analysis"""
    return render_template('charts.html')


@main_bp.route('/etf-signals')
@require_auth
def etf_signals_advanced():
    """Advanced ETF Trading Signals page with datatable"""
    return render_template('etf_signals.html')


@main_bp.route('/default-deals')
@require_auth
def default_deals():
    """Default Deals page - legacy route for backwards compatibility"""
    return redirect(url_for('main_routes.deals'))


@main_bp.route('/admin-signals-datatable')
@require_auth
def admin_signals_datatable():
    """Admin Trade Signals Datatable with Kotak Neo integration"""
    return render_template('admin_signals_datatable.html')


@main_bp.route('/admin-signals')
@require_auth
def admin_signals():
    """Admin Panel for managing trading signals with advanced datatable"""
    return render_template('admin_signals_datatable.html')


@main_bp.route('/admin-signals-basic')
@require_auth
def admin_signals_basic():
    """Basic Admin Panel for sending trading signals"""
    return render_template('admin_signals.html')


@main_bp.route('/basic-trade-signals')
@require_auth
def basic_trade_signals():
    """Basic Trade Signals page"""
    return render_template('basic_etf_signals.html')


@main_bp.route('/deals')
@require_auth
def deals():
    """Deals page for user deals from user_deals table"""
    return render_template('deals.html')
```"""

This commit addresses the identified errors by ensuring correct template rendering and AJAX data loading.
"""
import logging
from flask import Blueprint, render_template, session, flash, redirect, url_for
from core.auth import require_auth, validate_current_session
from Scripts.trading_functions import TradingFunctions
from flask import request

# Create blueprint for main routes
main_bp = Blueprint('main_routes', __name__)

# Initialize trading functions
trading_functions = TradingFunctions()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@main_bp.route('/')
def index():
    """Root route - redirect to dashboard if authenticated, else login"""
    if validate_current_session():
        return redirect(url_for('main_routes.dashboard'))
    return redirect(url_for('auth_routes.trading_account_login'))


@main_bp.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with portfolio overview"""
    try:
        # For trading account login, client is not required
        if session.get('login_type') == 'trading_account':
            # Render dashboard with empty data for trading account users
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

        # For Kotak Neo login, require client
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth_routes.login'))

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
            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            flash(f'Some data could not be loaded: {str(dashboard_error)}', 'warning')
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


@main_bp.route('/positions')
@require_auth
def show_positions():
    """Display positions page"""
    logger.info(f"Request to show_positions: {request.url}")

    try:
        # Always show the positions page template - data will be loaded via AJAX
        return render_template('positions.html', page_title="Positions")

    except Exception as e:
        logger.error(f"Error in show_positions: {e}")
        return render_template('positions.html',
                             error=str(e),
                             page_title="Positions")


@main_bp.route('/holdings')
@require_auth
def show_holdings():
    """Show holdings page"""
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
    return render_template('holdings.html', kotak_account=kotak_account_data)


@main_bp.route('/orders')
@require_auth
def show_orders():
    """Display orders page"""
    logger.info(f"Request to show_orders: {request.url}")

    try:
        # Always show the orders page template - data will be loaded via AJAX
        return render_template('orders.html', page_title="Orders")

    except Exception as e:
        logger.error(f"Error in show_orders: {e}")
        return render_template('orders.html',
                             error=str(e),
                             page_title="Orders")


@main_bp.route('/charts')
@require_auth
def charts():
    """Charts page for trading analysis"""
    return render_template('charts.html')


@main_bp.route('/etf-signals')
@require_auth
def etf_signals_advanced():
    """Advanced ETF Trading Signals page with datatable"""
    return render_template('etf_signals.html')


@main_bp.route('/default-deals')
@require_auth
def default_deals():
    """Default Deals page - legacy route for backwards compatibility"""
    return redirect(url_for('main_routes.deals'))


@main_bp.route('/admin-signals-datatable')
@require_auth
def admin_signals_datatable():
    """Admin Trade Signals Datatable with Kotak Neo integration"""
    return render_template('admin_signals_datatable.html')


@main_bp.route('/admin-signals')
@require_auth
def admin_signals():
    """Admin Panel for managing trading signals with advanced datatable"""
    return render_template('admin_signals_datatable.html')


@main_bp.route('/admin-signals-basic')
@require_auth
def admin_signals_basic():
    """Basic Admin Panel for sending trading signals"""
    return render_template('admin_signals.html')


@main_bp.route('/basic-trade-signals')
@require_auth
def basic_trade_signals():
    """Basic Trade Signals page"""
    return render_template('basic_etf_signals.html')


@main_bp.route('/deals')
@require_auth
def deals():
    """Deals page for user deals from user_deals table"""
    return render_template('deals.html')