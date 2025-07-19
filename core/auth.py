"""
Authentication core module for Kotak Neo Trading Platform
Handles session validation, authentication decorators, and user management
"""
import logging
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from Scripts.neo_client import NeoClient
from Scripts.user_manager import UserManager
from Scripts.session_helper import SessionHelper

# Initialize components
neo_client = NeoClient()
user_manager = UserManager()
session_helper = SessionHelper()


def validate_current_session():
    """Validate current session and check expiration"""
    try:
        # Check if user is authenticated with either method
        if not (session.get('authenticated') or session.get('kotak_logged_in')):
            logging.debug("Session not authenticated")
            return False
            
        # Check for required session fields directly in Flask session
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
            return redirect(url_for('auth_routes.login'))
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


def login_user(client_data, login_response):
    """Handle user login and session creation"""
    try:
        # Store client in session
        session['client'] = client_data
        session.permanent = True
        
        # Create or update user in database
        if login_response:
            db_user = user_manager.create_or_update_user(login_response)
            user_session = user_manager.create_user_session(db_user.id, login_response)
            
            session['db_user_id'] = db_user.id
            session['db_session_id'] = user_session.session_id
            
            logging.info(f"User logged in successfully: {client_data.get('ucc')}")
        
        return True
        
    except Exception as e:
        logging.error(f"Login user error: {e}")
        return False


def logout_user():
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