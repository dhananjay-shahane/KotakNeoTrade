"""
Database models for Kotak Neo trading account integration
"""
from datetime import datetime
from models import db
from flask_login import UserMixin

class KotakAccount(db.Model):
    """Model for storing Kotak Neo account information"""
    __tablename__ = 'kotak_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Kotak account details
    mobile_number = db.Column(db.String(15), nullable=False)
    ucc = db.Column(db.String(20), nullable=False)  # User Client Code
    account_name = db.Column(db.String(100), nullable=True)
    
    # Authentication status
    is_active = db.Column(db.Boolean, default=True)
    is_logged_in = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Session management
    session_token = db.Column(db.String(500), nullable=True)
    session_expires = db.Column(db.DateTime, nullable=True)
    
    # Account metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with main user
    user = db.relationship('User', backref='kotak_accounts')
    
    def __repr__(self):
        return f'<KotakAccount {self.ucc}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ucc': self.ucc,
            'mobile_number': self.mobile_number,
            'account_name': self.account_name,
            'is_active': self.is_active,
            'is_logged_in': self.is_logged_in,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TradingSession(db.Model):
    """Model for tracking trading sessions"""
    __tablename__ = 'trading_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    kotak_account_id = db.Column(db.Integer, db.ForeignKey('kotak_accounts.id'), nullable=False)
    
    # Session details
    session_id = db.Column(db.String(100), nullable=False)
    access_token = db.Column(db.String(500), nullable=True)
    refresh_token = db.Column(db.String(500), nullable=True)
    
    # Session timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    kotak_account = db.relationship('KotakAccount', backref='trading_sessions')
    
    def __repr__(self):
        return f'<TradingSession {self.session_id}>'