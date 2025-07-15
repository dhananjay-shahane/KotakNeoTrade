"""
Database configuration for real data connections
"""

import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration from environment variables
DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'trading_platform')
DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')

# External database URL for real trading data
EXTERNAL_DATABASE_URL = os.getenv('EXTERNAL_DATABASE_URL', '')

# SQLAlchemy configuration
Base = declarative_base()

def get_database_url():
    """Get the database URL for SQLAlchemy"""
    if EXTERNAL_DATABASE_URL:
        return EXTERNAL_DATABASE_URL
    else:
        return f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

def create_database_engine():
    """Create SQLAlchemy engine for database connections"""
    database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    return engine

def create_database_session():
    """Create SQLAlchemy session for database operations"""
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def test_database_connection():
    """Test database connection"""
    try:
        engine = create_database_engine()
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False