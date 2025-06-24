"""Authentication utilities"""
import functools
from flask import session, redirect, url_for, flash
import logging

def login_required(f):
    """Decorator to require authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_current_session():
    """Validate current session without auto-login bypass"""
    try:
        # Check if user is authenticated
        if not session.get('authenticated'):
            return False
            
        # Check if required session data exists
        required_fields = ['access_token', 'session_token', 'ucc']
        for field in required_fields:
            if not session.get(field):
                logging.warning(f"Missing session field: {field}")
                return False
                
        return True
    except Exception as e:
        logging.error(f"Session validation error: {str(e)}")
        return False

def clear_session():
    """Clear all session data"""
    session.clear()

def get_session_user_id():
    """Get current user's database ID from session"""
    return session.get('db_user_id')

def get_session_ucc():
    """Get current user's UCC from session"""
    return session.get('ucc')

def is_session_expired():
    """Check if current session is expired"""
    expires_at = session.get('session_expires_at')
    if not expires_at:
        return False
    
    from datetime import datetime
    try:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        return datetime.utcnow() > expires_at
    except Exception:
        return True