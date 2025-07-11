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
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor
        )
        return conn
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None