"""
Kotak Neo Trading Platform - Main Flask Application
Migrated for Replit environment compatibility
"""

import os
import sys
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)

# Configure session secret
app.secret_key = os.environ.get("SESSION_SECRET", "replit-kotak-neo-secret-2025")

# Configure for Replit proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Import models and create tables
with app.app_context():
    try:
        # Import all models to ensure tables are created
        import models
        from Scripts import models as script_models
        from Scripts import models_etf
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

# Import and register routes after app initialization
try:
    from routes.main_routes import main_bp
    from routes.auth_routes import auth_bp
    from routes.settings_routes import settings_routes
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_routes)
    print("✅ Main routes registered")
except ImportError as e:
    print(f"⚠️ Route import warning: {e}")

# Import API routes with error handling for each blueprint
api_blueprints = []

# Try to import each API blueprint individually
try:
    from api.dashboard_api import dashboard_bp
    api_blueprints.append(dashboard_bp)
except ImportError as e:
    print(f"⚠️ Dashboard API import warning: {e}")

try:
    from api.deals_api import deals_bp
    api_blueprints.append(deals_bp)
except ImportError as e:
    print(f"⚠️ Deals API import warning: {e}")

try:
    from api.market_watch_api import market_watch_bp
    api_blueprints.append(market_watch_bp)
except ImportError as e:
    print(f"⚠️ Market Watch API import warning: {e}")

try:
    from api.portfolio_api import portfolio_bp
    api_blueprints.append(portfolio_bp)
except ImportError as e:
    print(f"⚠️ Portfolio API import warning: {e}")

try:
    from api.default_deals_api import default_deals_api
    api_blueprints.append(default_deals_api)
except ImportError as e:
    print(f"⚠️ Default Deals API import warning: {e}")

try:
    from api.password_reset_api import password_reset_bp
    api_blueprints.append(password_reset_bp)
except ImportError as e:
    print(f"⚠️ Password Reset API import warning: {e}")

try:
    from api.health_check import health_bp
    api_blueprints.append(health_bp)
except ImportError as e:
    print(f"⚠️ Health Check API import warning: {e}")

# Register all successfully imported blueprints
for blueprint in api_blueprints:
    try:
        app.register_blueprint(blueprint)
        print(f"✅ Registered {blueprint.name}")
    except Exception as e:
        print(f"⚠️ Blueprint registration warning for {blueprint.name}: {e}")

print(f"✅ API routes registered ({len(api_blueprints)} blueprints)")

# Configure response headers for Replit compatibility
@app.after_request
def after_request(response):
    # Remove frame restrictions for Replit webview
    response.headers.pop('X-Frame-Options', None)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

if __name__ == '__main__':
    print("🚀 Starting Kotak Neo Trading Platform on Replit...")
    app.run(host='0.0.0.0', port=5000, debug=True)