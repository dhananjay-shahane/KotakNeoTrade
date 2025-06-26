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
    # Import etf_bp after app initialization to avoid circular imports
    from api.admin import admin_bp
    from api.deals import deals_bp
    from api.notifications import notifications_bp
    from api.supabase_api import supabase_bp
    from api.admin_signals_api import admin_signals_bp
    from api.signals_datatable import datatable_bp as signals_datatable_bp
    from api.enhanced_etf_signals import enhanced_etf_bp
    
    # Import realtime quotes after creating the manager
    from api.realtime_quotes import quotes_bp as realtime_bp

    # Check if blueprints are already registered to avoid duplicates
    registered_blueprints = [bp.name for bp in app.blueprints.values()]
    
    if 'auth' not in registered_blueprints:
        app.register_blueprint(auth_bp)
    if 'main' not in registered_blueprints:
        app.register_blueprint(main_bp)
    if 'dashboard_api' not in registered_blueprints:
        app.register_blueprint(dashboard_bp)
    if 'trading_api' not in registered_blueprints:
        app.register_blueprint(trading_bp)
    # Register ETF blueprint
    try:
        import sys
        import importlib

        # Force reload the ETF signals module to ensure clean import
        if 'api.etf_signals' in sys.modules:
            importlib.reload(sys.modules['api.etf_signals'])

        from api.etf_signals import etf_bp

        # Remove any existing ETF blueprint registration
        if 'etf' in app.blueprints:
            del app.blueprints['etf']

        app.register_blueprint(etf_bp)
        print("✓ ETF signals blueprint registered successfully")

        # Verify the /etf/signals route exists
        etf_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/etf/')]
        if etf_routes:
            print(f"✓ ETF routes registered: {etf_routes}")
        else:
            print("✗ No ETF routes found after registration")

    except Exception as etf_error:
        print(f"✗ ETF blueprint registration failed: {etf_error}")
        import traceback
        traceback.print_exc()
    # Register additional blueprints only if not already registered
    if 'admin' not in registered_blueprints:
        app.register_blueprint(admin_bp)
    if 'quotes' not in registered_blueprints:
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
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    try:
        print("🚀 Starting Flask application...")

        # Start real-time quotes scheduler
        try:
            from realtime_quotes_manager import realtime_quotes_manager
            realtime_quotes_manager.start()
            print("📊 Real-time quotes scheduler started")
        except ImportError:
            print("⚠️  Real-time quotes manager not available, skipping")

        # Start Yahoo Finance scheduler
        from yahoo_scheduler import start_yahoo_scheduler
        start_yahoo_scheduler()
        print("📈 Yahoo Finance scheduler started")

        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        print(f"🌐 Application will be available at:")
        print(f"   Local: http://0.0.0.0:{port}")
        if os.environ.get('REPLIT_DOMAINS'):
            print(f"   External: https://{os.environ.get('REPLIT_DOMAINS')}")

        # Run with proper Replit configuration
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()

