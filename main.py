"""
Unified Flask application combining root template and Kotak Neo Trading Platform
Shows the portfolio page by default with professional sidebar and header
Includes full Kotak Neo project integration on same port
"""

import os
import sys
from flask import Flask, render_template, redirect, url_for, request, flash

# Add kotak_neo_project to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kotak_neo_project'))

# Create Flask app with multiple template folders
from flask import Flask
import jinja2

# Configure template loader for multiple directories
template_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader('templates'),
    jinja2.FileSystemLoader('kotak_neo_project/templates'),
])

app = Flask(__name__, template_folder='templates', static_folder='static')
app.jinja_loader = template_loader
app.secret_key = os.environ.get("SESSION_SECRET", "demo-secret-key-2025")

# Configure for production
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for API endpoints
app.config['DEBUG'] = True

# Configure database for Kotak Neo integration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///./trading_platform.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Add static file routes for Kotak Neo project
@app.route('/kotak/static/<path:filename>')
def kotak_static(filename):
    """Serve static files for Kotak Neo project"""
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.join('kotak_neo_project', 'static'), filename)

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

# Setup library paths for Kotak Neo project compatibility
def setup_library_paths():
    """Configure library paths for pandas/numpy dependencies"""
    library_path = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    os.environ['LD_LIBRARY_PATH'] = library_path

# Setup environment before importing Kotak Neo modules
setup_library_paths()

# Import and register Kotak Neo blueprints
def register_kotak_neo_blueprints():
    """Register Kotak Neo project blueprints"""
    try:
        # Add Kotak Neo project paths for proper imports
        kotak_path = os.path.join(os.path.dirname(__file__), 'kotak_neo_project')
        if kotak_path not in sys.path:
            sys.path.insert(0, kotak_path)
        
        # Import blueprints first to avoid database conflicts
        from kotak_neo_project.routes.auth_routes import auth_bp
        from kotak_neo_project.routes.main_routes import main_bp
        
        # Register blueprints with URL prefix
        app.register_blueprint(auth_bp, url_prefix='/kotak')
        app.register_blueprint(main_bp, url_prefix='/kotak')
        
        # Initialize database after blueprints are registered
        try:
            from kotak_neo_project.core.database import db as kotak_db
            kotak_db.init_app(app)
            
            with app.app_context():
                kotak_db.create_all()
                print("Kotak Neo database initialized successfully")
        except Exception as e:
            print(f"Database initialization optional: {e}")
        
        # Add redirect routes
        @app.route('/kotak')
        @app.route('/kotak/')
        def kotak_neo_index():
            """Redirect to Kotak Neo login"""
            return redirect('/kotak/login')
            
        print("Successfully registered Kotak Neo blueprints")
        
    except Exception as e:
        print(f"Error registering Kotak Neo blueprints: {e}")
        # Fallback to simple redirect
        @app.route('/kotak')
        @app.route('/kotak/')
        def kotak_neo_index():
            """Simple redirect to Kotak Neo project"""
            flash('Kotak Neo project integration is being configured. Please check back shortly.', 'info')
            return redirect(url_for('portfolio'))

# Register the blueprints
register_kotak_neo_blueprints()

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




