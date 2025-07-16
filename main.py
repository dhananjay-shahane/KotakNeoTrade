"""
Unified Flask application combining root template and Kotak Neo Trading Platform
Shows the portfolio page by default with professional sidebar and header
Includes full Kotak Neo project integration on same port
"""

import os
import sys
from flask import Flask, render_template, redirect, url_for, request, flash

# Add kotak_neo_project to Python path for imports - but prioritize root level imports
root_path = os.path.dirname(__file__)
kotak_path = os.path.join(root_path, 'kotak_neo_project')
if root_path not in sys.path:
    sys.path.insert(0, root_path)
if kotak_path not in sys.path:
    sys.path.append(kotak_path)  # Append instead of insert to prioritize root

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

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')

# Configure database for both root app and Kotak Neo integration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///./trading_platform.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize Flask-Login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Flask-Mail
from flask_mail import Mail
mail = Mail(app)

# Initialize database for root app
from models import db, User, init_db
from kotak_models import KotakAccount, TradingSession
init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add static file routes for Kotak Neo project
@app.route('/kotak/static/<path:filename>')
def kotak_static(filename):
    """Serve static files for Kotak Neo project"""
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.join('kotak_neo_project', 'static'), filename)

@app.route('/')
def index():
    """Home page - check if user is logged in"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('portfolio'))
    else:
        return redirect(url_for('login'))

@app.route('/portfolio')
def portfolio():
    """Portfolio page - requires login"""
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('portfolio.html')

@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page - requires login"""
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('trading_signals.html')

@app.route('/deals')
def deals():
    """Deals page - requires login"""
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('deals.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    from api.auth_api import handle_login
    return handle_login()

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    from api.auth_api import handle_register, EmailService

    # Configure email service if credentials are available
    mail = None
    try:
        if os.environ.get('MAIL_USERNAME'):
            mail = EmailService.configure_mail(app)
    except Exception as e:
        print(f"Email configuration failed: {e}")

    return handle_register(mail)

@app.route('/logout')
def logout():
    """User logout"""
    from api.auth_api import handle_logout
    return handle_logout()

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

# API endpoints for authentication
@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    """API endpoint for login via AJAX"""
    from api.auth_api import login_api
    return login_api()

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    """API endpoint for registration via AJAX"""
    from api.auth_api import register_api
    return register_api(mail)

@app.route('/api/auth/status')
def api_auth_status():
    """API endpoint to check authentication status"""
    from api.auth_api import check_user_status
    return check_user_status()

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

# Register Kotak API blueprint
from api.kotak_api import kotak_api
app.register_blueprint(kotak_api)

# Kotak Neo Trading Routes
@app.route('/kotak/orders')
def kotak_orders():
    """Orders page from Kotak Neo project"""
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('kotak_orders.html')

@app.route('/kotak/positions')
def kotak_positions():
    """Positions page from Kotak Neo project"""
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('kotak_positions.html')

@app.route('/kotak/holdings')
def kotak_holdings():
    """Holdings page from Kotak Neo project"""
    from flask_login import login_required, current_user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('kotak_holdings.html')

@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page"""
    return render_template('base.html'), 404

# Modified the main block to initialize the external database table
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # Initialize external database table
    from api.auth_api import create_external_users_table
    if create_external_users_table():
        print("External users table created successfully")
    else:
        print("Failed to create external users table")

    # Configure email service
    from api.auth_api import EmailService
    mail = EmailService.configure_mail(app)

    # Register blueprints
    from api.auth_api import auth_blueprint
    from api.signals_api import signals_blueprint
    from api.deals_api import deals_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(signals_blueprint)
    app.register_blueprint(deals_blueprint)

    print("Application started successfully")
    app.run(host='0.0.0.0', port=5000, debug=True)