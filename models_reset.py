"""
Password Reset Token Model
Handles secure password reset tokens for user authentication
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app import db
import secrets
import hashlib

class PasswordResetToken(db.Model):
    """Model for storing password reset tokens"""
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('external_users.id'), nullable=False)
    token_hash = Column(String(128), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with user
    user = relationship("User", backref="reset_tokens")
    
    @staticmethod
    def generate_token():
        """Generate a secure 64-character token"""
        return secrets.token_urlsafe(48)  # 64 chars when base64 encoded
    
    @staticmethod
    def hash_token(token):
        """Hash the token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @classmethod
    def create_reset_token(cls, user_id, expiry_minutes=15):
        """Create a new password reset token for a user"""
        # Invalidate any existing tokens for this user
        existing_tokens = cls.query.filter_by(user_id=user_id, used=False).all()
        for token in existing_tokens:
            token.used = True
        
        # Generate new token
        raw_token = cls.generate_token()
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        
        # Create new token record
        reset_token = cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        db.session.add(reset_token)
        db.session.commit()
        
        return raw_token  # Return the raw token for sending via email
    
    @classmethod
    def validate_token(cls, token):
        """Validate a password reset token"""
        token_hash = cls.hash_token(token)
        
        reset_token = cls.query.filter_by(
            token_hash=token_hash,
            used=False
        ).first()
        
        if not reset_token:
            return None, "Invalid or already used token"
        
        if datetime.utcnow() > reset_token.expires_at:
            return None, "Token has expired"
        
        return reset_token, None
    
    def mark_as_used(self):
        """Mark the token as used"""
        self.used = True
        db.session.commit()