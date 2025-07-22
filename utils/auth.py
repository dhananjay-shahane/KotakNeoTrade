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
            return redirect(url_for('auth.trading_account_login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_current_session():
    """Validate current session with expiration check"""
    try:
        # Check if user is authenticated with either method
        if not (session.get('authenticated') or session.get('kotak_logged_in')):
            logging.debug("Session validation failed: Not authenticated")
            return False
            
        # Check if session has expired
        if is_session_expired():
            logging.info("Session has expired")
            return False
            
        # Check if required session data exists
        required_fields = ['access_token', 'ucc']
        for field in required_fields:
            if not session.get(field):
                logging.warning(f"Missing session field: {field}")
                return False
                
        # Additional validation - check if tokens are not empty
        access_token = session.get('access_token')
        
        if not access_token:
            logging.warning("Empty access token")
            return False
            
        # Basic token validation (check it's not obviously invalid)
        if len(access_token) < 10:
            logging.warning("Invalid access token format - token too short")
            return False
            
        # Check for session_token or sid (at least one should be present)
        session_token = session.get('session_token')
        sid = session.get('sid')
        
        if not session_token and not sid:
            logging.warning("Missing session identifiers")
            return False
            
        # Validate UCC format
        ucc = session.get('ucc')
        if not ucc or len(ucc) < 5 or len(ucc) > 6 or not ucc.isalnum():
            logging.warning("Invalid UCC format in session")
            return False
                
        return True
    except Exception as e:
        logging.error(f"Session validation error: {str(e)}")
        return False

def clear_session():
    """Clear all session data completely"""
    try:
        # Clear all session keys individually first
        keys_to_clear = list(session.keys())
        for key in keys_to_clear:
            session.pop(key, None)
        
        # Clear the entire session
        session.clear()
        
        # Ensure session is not permanent
        session.permanent = False
        
        logging.debug("Session cleared successfully")
        
    except Exception as e:
        logging.error(f"Error clearing session: {str(e)}")
        # Force clear even if there's an error
        try:
            session.clear()
        except:
            pass

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