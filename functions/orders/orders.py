"""
Orders Functions
Contains all orders-related route functions
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
