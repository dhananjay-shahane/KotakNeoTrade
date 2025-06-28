"""Authentication routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import logging

from utils.auth import validate_current_session, clear_session
from Scripts.neo_client import NeoClient
from Scripts.user_manager import UserManager

auth_bp = Blueprint('auth', __name__)

# Initialize components
neo_client = NeoClient()
user_manager = UserManager()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with TOTP authentication only"""
    if request.method == 'GET':
        return render_template('login.html')

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

        # Clear any existing session first
        clear_session()
        
        # Execute TOTP login with proper validation
        result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)

        if result and result.get('success') and result.get('client') and result.get('session_data'):
            client = result['client']
            session_data = result['session_data']
            
            # Validate that we have proper authentication tokens
            if not session_data.get('access_token') or not session_data.get('session_token'):
                flash('Authentication failed: Invalid response from server', 'error')
                return render_template('login.html')

            # Store in session with expiration
            session['authenticated'] = True
            session['access_token'] = session_data.get('access_token')
            session['session_token'] = session_data.get('session_token')
            session['sid'] = session_data.get('sid')
            session['ucc'] = ucc
            session['client'] = client
            session['login_time'] = datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')
            session['greeting_name'] = session_data.get('greetingName', ucc)
            session['session_created_at'] = datetime.now().isoformat()
            session['session_expires_at'] = (datetime.now() + timedelta(hours=24)).isoformat()
            session.permanent = True

            # Validate the client
            try:
                validation_success = neo_client.validate_session(client)
                if not validation_success:
                    logging.warning("Session validation failed but login was successful - proceeding")
            except Exception as val_error:
                logging.warning(f"Session validation error (proceeding anyway): {val_error}")

            # Store additional user data
            session['rid'] = session_data.get('rid')
            session['user_id'] = session_data.get('user_id')
            session['client_code'] = session_data.get('client_code')
            session['is_trial_account'] = session_data.get('is_trial_account')

            # Store user data in database
            try:
                login_response = {
                    'success': True,
                    'data': {
                        'ucc': ucc,
                        'mobile_number': mobile_number,
                        'greeting_name': session_data.get('greetingName'),
                        'user_id': session_data.get('user_id'),
                        'client_code': session_data.get('client_code'),
                        'product_code': session_data.get('product_code'),
                        'account_type': session_data.get('account_type'),
                        'branch_code': session_data.get('branch_code'),
                        'is_trial_account': session_data.get('is_trial_account', False),
                        'access_token': session_data.get('access_token'),
                        'session_token': session_data.get('session_token'),
                        'sid': session_data.get('sid'),
                        'rid': session_data.get('rid')
                    }
                }

                db_user = user_manager.create_or_update_user(login_response)
                user_session = user_manager.create_user_session(db_user.id, login_response)

                session['db_user_id'] = db_user.id
                session['db_session_id'] = user_session.session_id

                logging.info(f"User data stored in database for UCC: {ucc}")

            except Exception as db_error:
                logging.error(f"Failed to store user data in database: {db_error}")

            flash('Successfully authenticated with TOTP!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            error_message = "Authentication failed"
            if result and result.get('message'):
                error_message = f'TOTP login failed: {result.get("message")}'
            elif not result:
                error_message = "Authentication failed: No response from server"
            flash(error_message, 'error')
            return render_template('login.html')

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash(f'Login failed: {str(e)}', 'error')
        return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    clear_session()
    flash('Successfully logged out', 'success')
    return redirect(url_for('auth.login'))