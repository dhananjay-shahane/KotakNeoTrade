import os
import sys
import logging
import json
from datetime import datetime, timedelta
from functools import wraps
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import render_template, redirect, url_for, session, flash
from Scripts.trading_functions import TradingFunctions

trading_functions = TradingFunctions()

def dashboard():
    """Main dashboard with portfolio overview"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth_routes.trading_account_login'))

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