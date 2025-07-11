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
        # Use external PostgreSQL database from user
        external_db_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"
        
        logger.info("🔗 Connecting to external PostgreSQL database")
        conn = psycopg2.connect(
            external_db_url,
            cursor_factory=RealDictCursor
        )
        logger.info("✅ Successfully connected to external database")
        return conn
        
    except Exception as e:
        logger.error(f"❌ External database connection failed: {e}")
        # Fallback to local database
        try:
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(
                    database_url,
                    cursor_factory=RealDictCursor
                )
                logger.info("✅ Connected to local PostgreSQL database")
                return conn
        except Exception as local_e:
            logger.error(f"❌ Local database connection also failed: {local_e}")
            return None
        return None