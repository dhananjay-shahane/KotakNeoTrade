"""
Dashboard API endpoints for Kotak Neo Trading Platform
Handles all dashboard-related API calls and data fetching
"""
import logging
from flask import Blueprint, jsonify, session
from Scripts.trading_functions import TradingFunctions

# Create blueprint for dashboard API
dashboard_bp = Blueprint('dashboard_api', __name__, url_prefix='/api')

# Initialize trading functions
trading_functions = TradingFunctions()


def validate_session():
    """Validate current user session"""
    return session.get('client') is not None


@dashboard_bp.route('/dashboard-data')
def get_dashboard_data():
    """AJAX endpoint for dashboard data without page refresh"""
    if not validate_session():
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


@dashboard_bp.route('/holdings')
def get_holdings():
    """API endpoint to get holdings"""
    if not validate_session():
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


@dashboard_bp.route('/positions')
def get_positions():
    """API endpoint to get positions"""
    if not validate_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        positions = trading_functions.get_positions(client)
        return jsonify(positions)
    except Exception as e:
        logging.error(f"Positions API error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/orders')
def get_orders():
    """API endpoint to get orders"""
    if not validate_session():
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400

        orders = trading_functions.get_orders(client)
        return jsonify(orders)
    except Exception as e:
        logging.error(f"Orders API error: {e}")
        return jsonify({'error': str(e)}), 500