"""
Main application entry point for Kotak Neo Trading Platform
Handles environment setup, library paths, and blueprint registration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def setup_library_paths():
    """
    Configure library paths for pandas/numpy dependencies
    Required for Replit environment compatibility
    """
    library_path = '/nix/store/xvzz97yk73hw03v5dhhz3j47ggwf1yq1-gcc-13.2.0-lib/lib:/nix/store/026hln0aq1hyshaxsdvhg0kmcm6yf45r-zlib-1.2.13/lib'
    os.environ['LD_LIBRARY_PATH'] = library_path
    print(f"Set LD_LIBRARY_PATH: {library_path}")

# Setup environment before importing Flask modules
setup_library_paths()

# Import main Flask application
from app_clean import app

def register_blueprints():
    """
    Register all application blueprints for different features
    - Authentication and main routes
    - Trading API endpoints
    - ETF signals and admin panels
    - Real-time data and notifications
    """
    try:
        # Core application routes
        from routes.auth import auth_bp
        from routes.main import main_bp
        
        # API endpoints
        from api.dashboard import dashboard_api as dashboard_bp
        from api.trading import trading_api
        from api.admin import admin_bp
        from api.deals import deals_bp
        from api.notifications import notifications_bp
        
        # ETF and signals
        from api.etf_signals import etf_bp
        from api.admin_signals_api import admin_signals_bp
        from api.enhanced_etf_signals import enhanced_etf_bp
        
        # Market data APIs
        from api.realtime_quotes import quotes_bp as realtime_bp
        
        # Data management - Google Finance, Yahoo Finance, and Supabase removed
        from api.signals_datatable import datatable_bp as signals_datatable_bp
        from api.datatable_updates import datatable_updates_bp
        from api.data_analysis import data_analysis_bp

        # Register all blueprints
        blueprints = [
            (auth_bp, 'auth'),
            (main_bp, 'main'),
            (dashboard_bp, 'dashboard_api'),
            (trading_api, 'trading_api'),
            (etf_bp, 'etf'),
            (admin_bp, 'admin'),
            (deals_bp, 'deals'),
            (notifications_bp, 'notifications'),
            (realtime_bp, 'quotes'),
            (admin_signals_bp, 'admin_signals'),
            (enhanced_etf_bp, 'enhanced_etf'),
            # Google Finance, Yahoo Finance, and Supabase removed
            (signals_datatable_bp, 'signals_datatable'),
            (datatable_updates_bp, 'datatable_updates'),
            (data_analysis_bp, 'data_analysis')
        ]
        
        # Register each blueprint if not already registered
        registered_blueprints = [bp.name for bp in app.blueprints.values()]
        
        for blueprint, name in blueprints:
            if name not in registered_blueprints:
                app.register_blueprint(blueprint)
        
        # Add the ETF signals data route to the main app
        @app.route('/api/etf-signals-data', methods=['GET'])
        def etf_signals_data():
            from api.etf_signals import get_etf_signals_data
            return get_etf_signals_data()
                
        print("✓ All blueprints registered successfully")
        
        # Verify ETF routes are available
        etf_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule.startswith('/etf/')]
        if etf_routes:
            print(f"✓ ETF routes available: {len(etf_routes)} endpoints")
        
    except Exception as e:
        print(f"✗ Error registering blueprints: {e}")
        import traceback
        traceback.print_exc()

def start_schedulers():
    """
    Start background schedulers for market data updates
    - Real-time quotes manager (if available)
    - Yahoo Finance price updates
    """
    try:
        # Start real-time quotes scheduler
        try:
            from Scripts.realtime_quotes_manager import realtime_quotes_manager
            realtime_quotes_manager.start()
            print("📊 Real-time quotes scheduler started")
        except ImportError:
            print("⚠️ Real-time quotes manager not available")
        
        # Google Finance and Yahoo Finance schedulers removed - using Kotak Neo API only
        print("✅ Market data will be provided by Kotak Neo API only")
            
    except Exception as e:
        print(f"⚠️ Scheduler startup error: {e}")

if __name__ == '__main__':
    try:
        print("🚀 Starting Kotak Neo Trading Platform...")
        
        # Register all application blueprints
        register_blueprints()
        
        # Start background schedulers
        start_schedulers()
        
        # Configure server settings
        port = int(os.environ.get('PORT', 5000))
        
        print(f"🌐 Server starting on:")
        print(f"   Local: http://0.0.0.0:{port}")
        if os.environ.get('REPLIT_DOMAINS'):
            print(f"   External: https://{os.environ.get('REPLIT_DOMAINS')}")
        
        # Start Flask application server
        app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
        
    except Exception as e:
        print(f"❌ Application startup failed: {str(e)}")
        import traceback
        traceback.print_exc()