"""Database configuration and initialization"""
import os
import logging
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def get_db_connection():
    """Get database connection using psycopg2"""
    import psycopg2
    import psycopg2.extras

    try:
        # Database connection parameters
        db_params = {
            'host': os.environ.get('DATABASE_HOST', 'localhost'),
            'port': os.environ.get('DATABASE_PORT', '5432'),
            'database': os.environ.get('DATABASE_NAME', 'trading_db'),
            'user': os.environ.get('DATABASE_USER', 'postgres'),
            'password': os.environ.get('DATABASE_PASSWORD', 'password')
        }

        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None

def init_db(app):
    """Initialize database with Flask app"""
    try:
        # Set database URI before initializing
        db_uri = os.environ.get('DATABASE_URL')
        if not db_uri:
            # Fallback to SQLite for development
            db_uri = 'sqlite:///instance/trading_platform.db'

        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Only initialize if not already done
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            db.init_app(app)
        elif 'sqlalchemy' in app.extensions:
            # Already initialized, just update config
            app.extensions['sqlalchemy'].db = db

        logging.info("Database initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False