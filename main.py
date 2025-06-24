import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup library paths for pandas/numpy dependencies
def setup_library_paths():
    """Setup LD_LIBRARY_PATH for required libraries"""
    os.environ['LD_LIBRARY_PATH'] = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    print(f"Set LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")

# Setup environment before importing Flask modules
setup_library_paths()

from app import app  # noqa: F401

# Register blueprints only once to avoid conflicts
try:
    from routes.auth import auth_bp
    from routes.main import main_bp
    from api.dashboard import dashboard_api as dashboard_bp
    from api.trading import trading_api as trading_bp
    from api.etf_signals import etf_bp
    from api.admin import admin_bp
    from api.realtime_quotes import quotes_bp as realtime_bp
    from api.deals import deals_bp
    from api.notifications import notifications_bp
    from api.supabase_api import supabase_bp
    from api.admin_signals_api import admin_signals_bp
    from api.signals_datatable import datatable_bp as signals_datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp

    # Check if blueprints are already registered
    registered_blueprints = [bp.name for bp in app.blueprints.values()]

    if 'auth' not in registered_blueprints:
        app.register_blueprint(auth_bp)
    if 'main' not in registered_blueprints:
        app.register_blueprint(main_bp)
    if 'dashboard' not in registered_blueprints:
        app.register_blueprint(dashboard_bp)
    if 'trading' not in registered_blueprints:
        app.register_blueprint(trading_bp)
    if 'etf' not in registered_blueprints:
        app.register_blueprint(etf_bp)
    if 'admin' not in registered_blueprints:
        app.register_blueprint(admin_bp)
    if 'realtime' not in registered_blueprints:
        app.register_blueprint(realtime_bp)
    if 'deals' not in registered_blueprints:
        app.register_blueprint(deals_bp)
    if 'notifications' not in registered_blueprints:
        app.register_blueprint(notifications_bp)
    if 'supabase' not in registered_blueprints:
        app.register_blueprint(supabase_bp)
    if 'admin_signals' not in registered_blueprints:
        app.register_blueprint(admin_signals_bp)
    if 'signals_datatable' not in registered_blueprints:
        app.register_blueprint(signals_datatable_bp)
    if 'enhanced_etf' not in registered_blueprints:
        app.register_blueprint(enhanced_etf_bp)

    print("✓ Additional blueprints registered successfully")
except Exception as e:
    print(f"✗ Error registering blueprints: {e}")