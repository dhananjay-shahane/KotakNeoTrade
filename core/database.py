"""
Database configuration and initialization for Kotak Neo Trading Platform
Centralized database setup to avoid circular imports
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


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