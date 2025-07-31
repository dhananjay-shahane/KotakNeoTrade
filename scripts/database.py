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
    Uses centralized database configuration
    Returns a psycopg2 connection object
    """
    try:
        import sys
        sys.path.append('.')
        from config.database_config import get_db_dict_connection
        logger.info("🔗 Connecting to PostgreSQL database")
        conn = get_db_dict_connection()
        if conn:
            logger.info("✅ Successfully connected to database")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None