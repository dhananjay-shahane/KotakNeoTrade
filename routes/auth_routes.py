"""
Authentication routes for Kotak Neo Trading Platform
Handles login, logout, and authentication-related pages
"""
import logging
from datetime import datetime, timedelta
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
    """Login page with TOTP authentication"""
    if request.method == 'POST':
        try:
            # Get form data
            mobile_number = request.form.get('mobile_number', '').strip()
            ucc = request.form.get('ucc', '').strip()
            totp = request.form.get('totp', '').strip()
            mpin = request.form.get('mpin', '').strip()

            # Validate inputs
            if not all([mobile_number, ucc, totp, mpin]):
                flash('All fields are required', 'error')
                return render_template('login.html')

            # Validate formats
            if len(mobile_number) != 10 or not mobile_number.isdigit():
                flash('Mobile number must be 10 digits', 'error')
                return render_template('login.html')

            if len(totp) != 6 or not totp.isdigit():
                flash('TOTP must be 6 digits', 'error')
                return render_template('login.html')

            if len(mpin) != 6 or not mpin.isdigit():
                flash('MPIN must be 6 digits', 'error')
                return render_template('login.html')

            logging.info(f"Attempting login with UCC: {ucc}")

            # Execute TOTP login with all required parameters
            result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)
            
            if result and result.get('success'):
                client = result.get('client')
                session_data = result.get('session_data', {})

                if client:
                    # Store in Flask session
                    session['authenticated'] = True
                    session['access_token'] = session_data.get('access_token')
                    session['session_token'] = session_data.get('session_token')
                    session['sid'] = session_data.get('sid')
                    session['ucc'] = ucc
                    session['client'] = client
                    session.permanent = True

                    # Prepare login response for database storage
                    login_response = {
                        'success': True,
                        'data': {
                            'ucc': ucc,
                            'mobile_number': mobile_number,
                            'greeting_name': session_data.get('greetingName'),
                            'user_id': session_data.get('user_id'),
                            'client_code': session_data.get('client_code'),
                            'access_token': session_data.get('access_token'),
                            'session_token': session_data.get('session_token'),
                            'sid': session_data.get('sid'),
                            'rid': session_data.get('rid')
                        }
                    }

                    # Store user data in database
                    try:
                        db_user = user_manager.create_or_update_user(login_response)
                        user_session = user_manager.create_user_session(db_user.id, login_response)
                        
                        session['db_user_id'] = db_user.id
                        session['db_session_id'] = user_session.session_id
                        
                        logging.info(f"User data stored in database for UCC: {ucc}")
                    except Exception as db_error:
                        logging.error(f"Failed to store user data in database: {db_error}")

                    flash('Successfully authenticated with TOTP!', 'success')
                    return redirect(url_for('main_routes.dashboard'))
                else:
                    flash('Invalid client data received', 'error')
            else:
                error_msg = result.get('message', 'Authentication failed') if result else 'Login failed'
                flash(f'Login failed: {error_msg}', 'error')
                logging.error(f"Login failed for UCC {ucc}: {error_msg}")

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