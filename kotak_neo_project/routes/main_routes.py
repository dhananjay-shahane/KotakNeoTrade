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
    """Root route - go directly to dashboard without login"""
    return redirect(url_for('main_routes.dashboard'))


@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard with portfolio overview"""
    try:
        client = session.get('client')
        if not client:
            # Create a demo client for display purposes
            client = "demo_client"

        # Fetch dashboard data with error handling
        dashboard_data = {}
        try:
            if client == "demo_client":
                # Provide demo data for display
                raw_dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': []
                }
            else:
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
def show_positions():
    """Show positions page"""
    return render_template('positions.html')


@main_bp.route('/holdings')
def show_holdings():
    """Show holdings page"""
    return render_template('holdings.html')


@main_bp.route('/orders')
def show_orders():
    """Show orders page"""
    return render_template('orders.html')


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