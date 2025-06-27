"""Dashboard API endpoints"""
from flask import Blueprint, jsonify, session
import logging

from utils.auth import login_required
from trading_functions import TradingFunctions

dashboard_api = Blueprint('dashboard_api', __name__, url_prefix='/api')

# Initialize components
trading_functions = TradingFunctions()

@dashboard_api.route('/dashboard_data')
@login_required
def get_dashboard_data_api():
    """AJAX endpoint for dashboard data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        # Get fresh dashboard data
        raw_dashboard_data = trading_functions.get_dashboard_data(client)
        
        # Ensure proper data structure
        if isinstance(raw_dashboard_data, dict):
            dashboard_data = raw_dashboard_data
            if not isinstance(dashboard_data.get('positions'), list):
                dashboard_data['positions'] = []
            if not isinstance(dashboard_data.get('holdings'), list):
                dashboard_data['holdings'] = []
        elif isinstance(raw_dashboard_data, list):
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
            dashboard_data = {
                'positions': [],
                'holdings': [],
                'limits': {},
                'recent_orders': [],
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0
            }
        
        # Add success flag
        dashboard_data['success'] = True
        return jsonify(dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/positions_data')
@login_required
def get_positions_data_api():
    """AJAX endpoint for positions data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        positions_data = trading_functions.get_positions(client)
        
        # Ensure proper structure
        if isinstance(positions_data, list):
            return jsonify({'positions': positions_data, 'total': len(positions_data)})
        elif isinstance(positions_data, dict) and 'data' in positions_data:
            return jsonify({'positions': positions_data['data'], 'total': len(positions_data['data'])})
        else:
            return jsonify({'positions': [], 'total': 0})

    except Exception as e:
        logging.error(f"Positions API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/holdings_data')
@login_required
def get_holdings_data_api():
    """AJAX endpoint for holdings data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        holdings_data = trading_functions.get_holdings(client)
        
        # Ensure proper structure
        if isinstance(holdings_data, list):
            return jsonify({'holdings': holdings_data, 'total': len(holdings_data)})
        elif isinstance(holdings_data, dict) and 'data' in holdings_data:
            return jsonify({'holdings': holdings_data['data'], 'total': len(holdings_data['data'])})
        else:
            return jsonify({'holdings': [], 'total': 0})

    except Exception as e:
        logging.error(f"Holdings API error: {str(e)}")
        return jsonify({'error': str(e)}), 500