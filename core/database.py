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
            # Ensure instance directory exists
            import os
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
            os.makedirs(instance_dir, exist_ok=True)
            # Fallback to SQLite for development
            db_uri = f'sqlite:///{os.path.join(instance_dir, "trading_platform.db")}'

        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize database with app
        db.init_app(app)
        logging.info("Database initialized successfully")

        return True
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False