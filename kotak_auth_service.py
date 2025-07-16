"""
Kotak Neo Authentication Service
Handles login, session management, and account verification
"""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import session, request, jsonify
from flask_login import current_user
from kotak_models import KotakAccount, TradingSession, db

class KotakAuthService:
    """Service for handling Kotak Neo authentication"""
    
    def __init__(self):
        self.base_url = "https://gw-napi.kotaksecurities.com"
        self.app_id = "kotakneo"
        
    def authenticate_user(self, mobile_number, ucc, mpin, totp_code):
        """
        Authenticate user with Kotak Neo credentials
        This would normally connect to Kotak Neo API
        For now, we'll simulate the authentication process
        """
        try:
            # Input validation
            if not all([mobile_number, ucc, mpin, totp_code]):
                return {
                    'success': False,
                    'error': 'All fields are required'
                }
            
            # Validate mobile number format
            if not mobile_number.isdigit() or len(mobile_number) != 10:
                return {
                    'success': False,
                    'error': 'Invalid mobile number format'
                }
            
            # Validate UCC format (5-6 characters alphanumeric)
            if len(ucc) < 5 or len(ucc) > 6:
                return {
                    'success': False,
                    'error': 'Invalid UCC format'
                }
            
            # Validate MPIN (6 digits)
            if not mpin.isdigit() or len(mpin) != 6:
                return {
                    'success': False,
                    'error': 'Invalid MPIN format'
                }
            
            # Validate TOTP (6 digits)
            if not totp_code.isdigit() or len(totp_code) != 6:
                return {
                    'success': False,
                    'error': 'Invalid TOTP code format'
                }
            
            # Simulate API call to Kotak Neo
            # In real implementation, this would make actual API calls
            session_token = self._generate_session_token()
            
            # Create or update Kotak account
            kotak_account = self._create_or_update_account(
                mobile_number, ucc, session_token
            )
            
            if kotak_account:
                # Create trading session
                trading_session = self._create_trading_session(
                    kotak_account.id, session_token
                )
                
                # Store session in Flask session
                session['kotak_session'] = {
                    'account_id': kotak_account.id,
                    'ucc': ucc,
                    'mobile_number': mobile_number,
                    'session_token': session_token,
                    'logged_in_at': datetime.utcnow().isoformat()
                }
                
                return {
                    'success': True,
                    'account': kotak_account.to_dict(),
                    'session_token': session_token,
                    'message': 'Successfully logged in to Kotak Neo'
                }
            
            return {
                'success': False,
                'error': 'Authentication failed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Authentication error: {str(e)}'
            }
    
    def _generate_session_token(self):
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def _create_or_update_account(self, mobile_number, ucc, session_token):
        """Create or update Kotak account for current user"""
        try:
            if not current_user.is_authenticated:
                return None
            
            # Check if account already exists
            existing_account = KotakAccount.query.filter_by(
                user_id=current_user.id,
                ucc=ucc
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.mobile_number = mobile_number
                existing_account.is_logged_in = True
                existing_account.last_login = datetime.utcnow()
                existing_account.session_token = session_token
                existing_account.session_expires = datetime.utcnow() + timedelta(hours=8)
                existing_account.updated_at = datetime.utcnow()
                
                db.session.commit()
                return existing_account
            else:
                # Create new account
                new_account = KotakAccount(
                    user_id=current_user.id,
                    mobile_number=mobile_number,
                    ucc=ucc,
                    account_name=f"Kotak Account {ucc}",
                    is_active=True,
                    is_logged_in=True,
                    last_login=datetime.utcnow(),
                    session_token=session_token,
                    session_expires=datetime.utcnow() + timedelta(hours=8)
                )
                
                db.session.add(new_account)
                db.session.commit()
                return new_account
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating/updating account: {str(e)}")
            return None
    
    def _create_trading_session(self, account_id, session_token):
        """Create a new trading session"""
        try:
            new_session = TradingSession(
                kotak_account_id=account_id,
                session_id=session_token,
                access_token=session_token,
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=8),
                is_active=True
            )
            
            db.session.add(new_session)
            db.session.commit()
            return new_session
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating trading session: {str(e)}")
            return None
    
    def logout_account(self, account_id):
        """Logout from Kotak account"""
        try:
            account = KotakAccount.query.get(account_id)
            if account and account.user_id == current_user.id:
                account.is_logged_in = False
                account.session_token = None
                account.session_expires = None
                
                # End active sessions
                active_sessions = TradingSession.query.filter_by(
                    kotak_account_id=account_id,
                    is_active=True
                ).all()
                
                for session_obj in active_sessions:
                    session_obj.is_active = False
                    session_obj.ended_at = datetime.utcnow()
                
                db.session.commit()
                
                # Clear Flask session
                if 'kotak_session' in session:
                    del session['kotak_session']
                
                return {'success': True, 'message': 'Successfully logged out'}
            
            return {'success': False, 'error': 'Account not found'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Logout error: {str(e)}'}
    
    def get_user_accounts(self):
        """Get all Kotak accounts for current user"""
        try:
            if not current_user.is_authenticated:
                return []
            
            accounts = KotakAccount.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).all()
            
            return [account.to_dict() for account in accounts]
            
        except Exception as e:
            print(f"Error getting user accounts: {str(e)}")
            return []
    
    def is_session_valid(self, account_id):
        """Check if session is still valid"""
        try:
            account = KotakAccount.query.get(account_id)
            if account and account.session_expires:
                return datetime.utcnow() < account.session_expires
            return False
            
        except Exception as e:
            print(f"Error checking session validity: {str(e)}")
            return False
    
    def get_current_session(self):
        """Get current Kotak session from Flask session"""
        return session.get('kotak_session')