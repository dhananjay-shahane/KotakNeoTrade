
"""
Authentication Middleware
Centralized authentication and authorization
"""
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, current_app
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Centralized authentication middleware"""
    
    @staticmethod
    def generate_session_token(user_data: Dict[str, Any]) -> str:
        """Generate secure JWT session token"""
        try:
            payload = {
                'user_id': user_data.get('user_id'),
                'username': user_data.get('username'),
                'ucc': user_data.get('ucc'),
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow(),
                'type': 'session'
            }
            
            secret_key = current_app.config.get('SECRET_KEY')
            if not secret_key:
                raise ValueError("SECRET_KEY not configured")
            
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None
    
    @staticmethod
    def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT session token"""
        try:
            secret_key = current_app.config.get('SECRET_KEY')
            if not secret_key:
                return None
            
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Verify token type
            if payload.get('type') != 'session':
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def validate_session() -> bool:
        """Enhanced session validation"""
        try:
            # Check basic session fields
            if not session.get('authenticated'):
                return False
            
            # Verify session token if present
            session_token = session.get('session_token')
            if session_token:
                payload = AuthMiddleware.verify_session_token(session_token)
                if not payload:
                    return False
            
            # Check session expiration
            expires_at = session.get('session_expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if datetime.now() > expires_at:
                    return False
            
            # Validate required fields
            required_fields = ['access_token', 'ucc']
            for field in required_fields:
                if not session.get(field):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    @staticmethod
    def clear_session():
        """Secure session cleanup"""
        try:
            # Store session ID for audit
            session_id = session.get('session_id')
            if session_id:
                logger.info(f"Clearing session: {session_id}")
            
            # Clear all session data
            session.clear()
            session.permanent = False
            
            logger.info("Session cleared successfully")
            
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    @staticmethod
    def require_auth(f):
        """Enhanced authentication decorator"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AuthMiddleware.validate_session():
                if request.is_json:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'Please login to access this resource',
                        'code': 'AUTH_REQUIRED'
                    }), 401
                else:
                    from flask import redirect, url_for, flash
                    flash('Please login to access this page', 'error')
                    return redirect(url_for('auth_routes.trading_account_login'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def require_role(required_role: str):
        """Role-based access control decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not AuthMiddleware.validate_session():
                    return jsonify({'error': 'Authentication required'}), 401
                
                user_role = session.get('user_role', 'user')
                if user_role != required_role and user_role != 'admin':
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_role': required_role,
                        'user_role': user_role
                    }), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def audit_log(action: str, details: Dict[str, Any] = None):
        """Log security-relevant actions"""
        try:
            user_id = session.get('user_id', 'anonymous')
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            audit_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'action': action,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'details': details or {}
            }
            
            logger.info(f"AUDIT: {audit_data}")
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")


# Security headers middleware
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
