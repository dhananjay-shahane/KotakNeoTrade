"""
Authentication routes for Kotak Neo Trading Platform
Handles login, logout, and authentication-related pages
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from core.auth import login_user, logout_user, validate_current_session
from Scripts.neo_client import NeoClient
from Scripts.user_manager import UserManager

# Create blueprint for auth routes
auth_bp = Blueprint('auth_routes', __name__)

# Initialize components
neo_client = NeoClient()
user_manager = UserManager()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with TOTP authentication only"""
    if request.method == 'POST':
        try:
            # Get TOTP token from form
            totp_token = request.form.get('totp_token', '').strip()
            
            if not totp_token:
                flash('TOTP token is required', 'error')
                return render_template('login.html')

            logging.info(f"Attempting TOTP login with token: {totp_token[:3]}...")

            # Validate TOTP with Neo Client
            result = neo_client.totp_login(totp_token)
            
            if result and result.get('success'):
                # Extract client data from result
                client_data = result.get('client')
                
                if client_data:
                    # Store session and create user
                    session_data = result.get('user_session', {})
                    
                    # Prepare login response for database storage
                    login_response = {
                        'success': True,
                        'user_data': {
                            'user_id': session_data.get('user_id'),
                            'ucc': session_data.get('ucc'),
                            'username': session_data.get('username'),
                            'email': session_data.get('email'),
                            'mobile': session_data.get('mobile'),
                            'pan': session_data.get('pan'),
                            'account_type': session_data.get('account_type'),
                            'branch_code': session_data.get('branch_code'),
                            'is_trial_account': session_data.get('is_trial_account', False),
                            'access_token': session_data.get('access_token'),
                            'session_token': session_data.get('session_token'),
                            'sid': session_data.get('sid'),
                            'rid': session_data.get('rid')
                        }
                    }

                    # Use core auth module to handle login
                    if login_user(client_data, login_response):
                        flash('Successfully authenticated with TOTP!', 'success')
                        return redirect(url_for('main_routes.dashboard'))
                    else:
                        flash('Failed to create user session', 'error')
                else:
                    flash('Invalid client data received', 'error')
            else:
                error_msg = result.get('message', 'Authentication failed') if result else 'Login failed'
                flash(f'TOTP login failed: {error_msg}', 'error')

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    if logout_user():
        flash('Logged out successfully', 'info')
    else:
        flash('Logout failed', 'error')
    return redirect(url_for('auth_routes.login'))