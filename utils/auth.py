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
    """Validate current session with expiration check"""
    try:
        # Check if user is authenticated
        if not session.get('authenticated'):
            return False
            
        # Check if session has expired
        if is_session_expired():
            logging.info("Session has expired")
            clear_session()
            return False
            
        # Check if required session data exists
        required_fields = ['access_token', 'session_token', 'ucc', 'client']
        for field in required_fields:
            if not session.get(field):
                logging.warning(f"Missing session field: {field}")
                clear_session()
                return False
                
        # Additional validation - check if tokens are not empty
        if not session.get('access_token') or not session.get('session_token'):
            logging.warning("Empty authentication tokens")
            clear_session()
            return False
                
        return True
    except Exception as e:
        logging.error(f"Session validation error: {str(e)}")
        clear_session()
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
        # If no expiration time set, consider it expired
        return True
    
    from datetime import datetime
    try:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        return datetime.now() > expires_at
    except Exception:
        logging.error("Error checking session expiration")
        return True