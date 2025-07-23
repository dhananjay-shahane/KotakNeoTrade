"""
Authentication core module for Kotak Neo Trading Platform
Handles session validation, authentication decorators, and user management
"""
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash, request, jsonify

def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Check if user is authenticated through any method
        if session.get('authenticated') or session.get('kotak_logged_in'):
            return True
        
        # Check session expiration
        if 'login_time' in session:
            login_time = session['login_time']
            if isinstance(login_time, str):
                login_time = datetime.fromisoformat(login_time)
            
            # Check if session is expired (24 hours)
            if datetime.utcnow() - login_time > timedelta(hours=24):
                session.clear()
                return False
        
        # Check if client exists
        if session.get('client'):
            return True
            
        return False
        
    except Exception as e:
        logging.error(f"Session validation error: {e}")
        session.clear()
        return False

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_current_session():
            return redirect(url_for('auth_routes.trading_account_login'))
        return f(*args, **kwargs)
    return decorated_function


def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Check if user is authenticated with either method
        if not (session.get('authenticated') or session.get('kotak_logged_in')):
            logging.debug("Session not authenticated")
            return False
            
        # For trading account login, check different required fields
        if session.get('login_type') == 'trading_account' and session.get('authenticated'):
            required_fields = ['access_token', 'username']
            for field in required_fields:
                if not session.get(field):
                    logging.debug(f"Missing required session field for trading account: {field}")
                    return False
        else:
            # For Kotak Neo login, check original required fields
            required_fields = ['access_token', 'ucc']
            for field in required_fields:
                if not session.get(field):
                    logging.debug(f"Missing required session field: {field}")
                    return False

        # Additional validation for token format
        access_token = session.get('access_token')
        if not access_token or len(access_token) < 10:
            logging.debug("Invalid access token format")
            return False

        # Session is valid
        return True

    except Exception as e:
        logging.error(f"Session validation error: {e}")
        return False


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_current_session():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page', 'error')
            return redirect(url_for('auth_routes.trading_account_login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current authenticated user information"""
    try:
        if not validate_current_session():
            return None
            
        client = session.get('client')
        if not client:
            return None
            
        # Get user information from session
        user_info = {
            'user_id': client.get('user_id'),
            'ucc': client.get('ucc'),
            'username': client.get('username'),
            'email': client.get('email'),
            'session_id': client.get('sid')
        }
        
        return user_info
        
    except Exception as e:
        logging.error(f"Error getting current user: {e}")
        return None


def login_user_session(client_data, login_response=None):
    """Handle user login and session creation"""
    try:
        # Store client in session
        session['client'] = client_data
        session['authenticated'] = True
        session['login_time'] = datetime.utcnow().isoformat()
        session.permanent = True
        
        # Store user data if available
        if login_response:
            session['ucc'] = login_response.get('ucc', '')
            session['greeting_name'] = login_response.get('greeting_name', 'User')
            session['mobile_number'] = login_response.get('mobile_number', '')
        
        logging.info(f"User logged in successfully: {client_data.get('ucc', 'unknown')}")
        return True
        
    except Exception as e:
        logging.error(f"Login user error: {e}")
        return False

def logout_user_session():
    """Handle user logout and session cleanup"""
    try:
        # Clear session
        session.clear()
        logging.info("User logged out successfully")
        return True
        
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return False


def check_session_health():
    """Check the health of current session"""
    try:
        if not validate_current_session():
            return False
            
        client = session.get('client')
        if not client:
            return False
            
        # Try to validate session with Neo API
        return neo_client.validate_session(client)
        
    except Exception as e:
        logging.error(f"Session health check failed: {e}")
        return False