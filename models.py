"""
Database models for user authentication system
"""
import os
import re
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import Flask
import secrets
import string
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def generate_username(cls, email, mobile):
        """Generate a unique username from email and mobile number"""
        # Take first 3 letters from email (before @)
        email_part = ''.join(filter(str.isalpha, email.split('@')[0]))[:3].lower()

        # Take last 2 digits from mobile
        mobile_part = mobile[-2:] if len(mobile) >= 2 else mobile

        # Combine to create 5-character username
        base_username = (email_part + mobile_part).ljust(5, '0')[:5]

        # Ensure uniqueness
        counter = 1
        username = base_username
        while cls.query.filter_by(username=username).first():
            username = base_username[:-1] + str(counter)
            counter += 1
            if counter > 9:  # Prevent infinite loop
                import random
                username = base_username[:-2] + str(random.randint(10, 99))
                break

        return username

    def __repr__(self):
        return f'<User {self.username}>'

    @staticmethod
    def generate_random_password(length=8):
        """Generate random password"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))


def init_db(app):
    """Initialize database with app"""
    db.init_app(app)

    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

# Make User available for import
__all__ = ['User', 'db', 'init_db']