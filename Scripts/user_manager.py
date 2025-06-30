from scripts.models import db, User, UserSession, UserPreferences
from datetime import datetime, timedelta
import json
import uuid

class UserManager:
    """Manages user data in PostgreSQL database"""
    
    def __init__(self):
        pass
    
    def create_or_update_user(self, login_response):
        """Create or update user from Kotak Neo login response"""
        try:
            # Extract user data from login response
            data = login_response.get('data', {})
            ucc = data.get('ucc')
            mobile_number = data.get('mobile_number', '')
            
            if not ucc:
                raise ValueError("UCC is required to create/update user")
            
            # Find existing user or create new one
            user = User.query.filter_by(ucc=ucc).first()
            if not user:
                user = User(ucc=ucc)
                db.session.add(user)
            
            # Update user information
            user.mobile_number = mobile_number
            user.greeting_name = data.get('greeting_name')
            user.user_id = data.get('user_id')
            user.client_code = data.get('client_code')
            user.product_code = data.get('product_code')
            user.account_type = data.get('account_type')
            user.branch_code = data.get('branch_code')
            user.is_trial_account = data.get('is_trial_account', False)
            
            # Update session tokens
            user.access_token = data.get('access_token')
            user.session_token = data.get('session_token')
            user.sid = data.get('sid')
            user.rid = data.get('rid')
            
            # Update timestamps
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            # Set session expiry (24 hours from now)
            user.session_expires_at = datetime.utcnow() + timedelta(hours=24)
            
            db.session.commit()
            
            # Create user preferences if they don't exist
            if not user.preferences:
                preferences = UserPreferences(user_id=user.id)
                db.session.add(preferences)
                db.session.commit()
            
            return user
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def create_user_session(self, user_id, login_response):
        """Create a new user session record"""
        try:
            session_id = str(uuid.uuid4())
            data = login_response.get('data', {})
            
            user_session = UserSession(
                user_id=user_id,
                session_id=session_id,
                access_token=data.get('access_token'),
                session_token=data.get('session_token'),
                sid=data.get('sid'),
                rid=data.get('rid'),
                login_response=json.dumps(login_response),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            db.session.add(user_session)
            db.session.commit()
            
            return user_session
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_user_by_ucc(self, ucc):
        """Get user by UCC"""
        return User.query.filter_by(ucc=ucc, is_active=True).first()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return User.query.filter_by(id=user_id, is_active=True).first()
    
    def get_active_session(self, user_id):
        """Get active session for user"""
        return UserSession.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).first()
    
    def invalidate_user_sessions(self, user_id):
        """Invalidate all sessions for a user"""
        try:
            UserSession.query.filter_by(user_id=user_id).update({'is_active': False})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_user_preferences(self, user_id, preferences_data):
        """Update user preferences"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            if not user.preferences:
                preferences = UserPreferences(user_id=user_id)
                db.session.add(preferences)
            else:
                preferences = user.preferences
            
            # Update preferences
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
            
            preferences.updated_at = datetime.utcnow()
            db.session.commit()
            
            return preferences
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_user_preferences(self, user_id):
        """Get user preferences"""
        user = User.query.get(user_id)
        if user and user.preferences:
            return user.preferences
        return None
    
    def clean_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            expired_sessions = UserSession.query.filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                session.is_active = False
            
            db.session.commit()
            return len(expired_sessions)
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_user_stats(self):
        """Get basic user statistics"""
        total_users = User.query.filter_by(is_active=True).count()
        active_sessions = UserSession.query.filter_by(is_active=True).filter(
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        return {
            'total_users': total_users,
            'active_sessions': active_sessions
        }
    
    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        try:
            user = User.query.get(user_id)
            if user:
                user.is_active = False
                user.updated_at = datetime.utcnow()
                
                # Invalidate all sessions
                self.invalidate_user_sessions(user_id)
                
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e