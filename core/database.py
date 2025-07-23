"""
Database configuration and initialization for Kotak Neo Trading Platform
Centralized database setup to avoid circular imports
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy database models"""
    pass


# Initialize database instance
db = SQLAlchemy(model_class=Base)


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Import models to ensure tables are created
        from Scripts import models
        from Scripts import models_etf
        db.create_all()
        
    return db


def get_db_connection():
    """
    Get a direct PostgreSQL connection for external operations
    Returns a psycopg2 connection object
    """
    try:
        # Use PostgreSQL database from environment variables
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            # Build URL from individual components
            host = os.environ.get('DB_HOST', 'dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com')
            database = os.environ.get('DB_NAME', 'kotak_trading_db')
            user = os.environ.get('DB_USER', 'kotak_trading_db_user')
            password = os.environ.get('DB_PASSWORD', 'JRUlk8RutdgVcErSiUXqljDUdK8sBsYO')
            port = os.environ.get('DB_PORT', '5432')
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        logger.info("🔗 Connecting to PostgreSQL database")
        
        # Try with SSL first
        try:
            conn = psycopg2.connect(
                database_url + "?sslmode=require",
                cursor_factory=RealDictCursor
            )
            logger.info("✅ Successfully connected to database with SSL")
            return conn
        except Exception as ssl_e:
            logger.warning(f"SSL connection failed: {ssl_e}, trying fallback")
            
            # Fallback without strict SSL
            try:
                conn = psycopg2.connect(
                    database_url + "?sslmode=prefer",
                    cursor_factory=RealDictCursor
                )
                logger.info("✅ Successfully connected to database (fallback)")
                return conn
            except Exception as fallback_e:
                logger.error(f"Fallback connection failed: {fallback_e}")
                raise fallback_e
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None