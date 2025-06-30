import os
import logging
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
from config.settings import get_config
config = get_config()
app.config.from_object(config)

# Configure for Replit deployment
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1, x_for=1, x_port=1)

# Initialize extensions
Session(app)

# Initialize database
from Scripts.models import db, User, UserSession, UserPreferences
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Import and register blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from api.dashboard import dashboard_api

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(dashboard_api)

# Import remaining API endpoints from original app.py
from api.trading import trading_api
from api.admin import admin_api

app.register_blueprint(trading_api)
app.register_blueprint(admin_api)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)