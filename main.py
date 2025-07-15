"""
Simple Flask application to demonstrate Kotak Neo template structure
Shows the portfolio page by default with professional sidebar and header
"""

import os
from flask import Flask, render_template, redirect, url_for

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "demo-secret-key-2025")

@app.route('/')
def index():
    """Home page - show portfolio by default"""
    return redirect(url_for('portfolio'))

@app.route('/portfolio')
def portfolio():
    """Portfolio page"""
    return render_template('portfolio.html')

@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page"""
    return render_template('trading_signals.html')

@app.route('/deals')
def deals():
    """Deals page"""
    return render_template('deals.html')

# API endpoints for ETF signals and deals functionality
@app.route('/api/etf-signals-data')
def api_etf_signals_data():
    """API endpoint for ETF signals data"""
    from api.signals_api import get_etf_signals_data
    return get_etf_signals_data()

@app.route('/api/deals/create-from-signal', methods=['POST'])
def api_create_deal_from_signal():
    """API endpoint to create deal from signal"""
    from api.signals_api import create_deal_from_signal
    return create_deal_from_signal()

@app.route('/api/deals-data')
def api_deals_data():
    """API endpoint for deals data"""
    from api.deals_api import get_deals_data
    return get_deals_data()

@app.route('/api/deals/update', methods=['POST'])
def api_update_deal():
    """API endpoint to update deal"""
    from api.deals_api import update_deal
    return update_deal()

@app.route('/api/deals/close', methods=['POST'])
def api_close_deal():
    """API endpoint to close deal"""
    from api.deals_api import close_deal
    return close_deal()

@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page"""
    return render_template('base.html'), 404

if __name__ == '__main__':
    print("Starting Kotak Neo Template Application...")
    print("Default page: Portfolio")
    app.run(host='0.0.0.0', port=5000, debug=True)




