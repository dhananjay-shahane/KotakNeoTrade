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

@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page"""
    return render_template('base.html'), 404

if __name__ == '__main__':
    print("Starting Kotak Neo Template Application...")
    print("Default page: Portfolio")
    app.run(host='0.0.0.0', port=5000, debug=True)