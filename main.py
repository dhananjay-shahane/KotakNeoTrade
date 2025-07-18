"""
Main Flask Application for Kotak Neo Trading Platform
"""
import os
import logging
from flask import Flask, render_template, session, redirect, url_for
from flask_login import LoginManager, login_required
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/trading_platform.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        # Simple user loader for demo
        return None

    # Register blueprints
    try:
        from routes.auth_routes import auth_bp
        from routes.main_routes import main_bp
        from api.kotak_api import kotak_api

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(main_bp)
        app.register_blueprint(kotak_api)

        logger.info("Successfully registered all blueprints")
    except ImportError as e:
        logger.error(f"Error importing blueprints: {e}")

    # Main routes
    @app.route('/')
    def index():
        """Home page"""
        return redirect(url_for('portfolio'))

    @app.route('/portfolio')
    def portfolio():
        """Portfolio page - main landing page"""
        return render_template('portfolio.html')

    @app.route('/trading_signals')
    def trading_signals():
        """Trading signals page"""
        return render_template('trading_signals.html')

    @app.route('/deals')
    def deals():
        """Deals page"""
        return render_template('deals.html')

    @app.route('/login')
    def login():
        """Login page"""
        return render_template('auth/login.html')

    @app.route('/register')
    def register():
        """Register page"""
        return render_template('auth/register.html')

    @app.route('/logout')
    def logout():
        """Logout"""
        session.clear()
        return redirect(url_for('portfolio'))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)