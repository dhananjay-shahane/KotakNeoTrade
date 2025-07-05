import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from flask import render_template, redirect, url_for, session, flash
from Scripts.trading_functions import TradingFunctions

trading_functions = TradingFunctions()


def positions():
    """Positions page"""
    try:
        client = session.get('client')
        if not client:
            return redirect(url_for('login'))

        positions_data = trading_functions.get_positions(client)

        if isinstance(positions_data, dict):
            positions_list = positions_data.get('data') or positions_data.get('positions', [])
        elif isinstance(positions_data, list):
            positions_list = positions_data
        else:
            positions_list = []

        print(f"Positions data: {positions_list}")
        return render_template('positions.html', positions=positions_list)

    except Exception as e:
        print(f"Positions page error: {e}")
        return positions()
