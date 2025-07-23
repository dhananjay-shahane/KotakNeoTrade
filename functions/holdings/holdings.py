"""
Holdings Functions
Contains all holdings-related route functions
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


from flask import render_template, redirect, url_for, session, flash
import logging
from Scripts.neo_client import NeoClient
from Scripts.trading_functions import TradingFunctions

neo_client = NeoClient()
trading_functions = TradingFunctions()

def holdings():
    """Holdings page"""

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth_routes.trading_account_login'))

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

