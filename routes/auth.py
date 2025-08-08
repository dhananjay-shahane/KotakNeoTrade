"""Authentication routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
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

        # Validate UCC format - should be alphanumeric and 5-6 characters
        if not ucc.isalnum() or len(ucc) < 5 or len(ucc) > 6:
            flash('Invalid UCC format. UCC should be 5-6 alphanumeric characters', 'error')
            return render_template('login.html')

        # Validate mobile number format
        if len(mobile_number) != 10 or not mobile_number.isdigit():
            flash('Mobile number must be 10 digits', 'error')
            return render_template('login.html')

        # Validate TOTP format
        if len(totp) != 6 or not totp.isdigit():
            flash('TOTP must be 6 digits', 'error')
            return render_template('login.html')

        # Validate MPIN format
        if len(mpin) != 6 or not mpin.isdigit():
            flash('MPIN must be 6 digits', 'error')
            return render_template('login.html')

        # Clear any existing session first
        clear_session()
        
        # Execute TOTP login with proper validation
        logging.info(f"Attempting login for UCC: {ucc}, Mobile: {mobile_number}")
        result = neo_client.execute_totp_login(mobile_number, ucc, totp, mpin)
        
        logging.info(f"Login result: {result}")

        # Handle login result
        if result and result.get('success'):
            logging.info("Login successful, processing session data...")
            
            # Get session data from result
            session_data = result.get('session_data', {})
            client = result.get('client')
            
            if not session_data and not client:
                logging.error("No session data or client in login result")
                flash('Authentication failed: Invalid login response', 'error')
                return render_template('login.html')
            
            # Extract tokens from either session_data or client
            access_token = session_data.get('access_token') or (client.access_token if hasattr(client, 'access_token') else None)
            session_token = session_data.get('session_token') or (client.session_token if hasattr(client, 'session_token') else None)
            sid = session_data.get('sid') or session_data.get('sId') or (client.sid if hasattr(client, 'sid') else None)
            
            if not access_token:
                logging.error("No access token found in login result")
                flash('Authentication failed: No access token received', 'error')
                return render_template('login.html')
                
        if result and result.get('success') and (result.get('client') or result.get('session_data')):
            client = result.get('client')
            session_data = result.get('session_data', {})
            
            # Validate we have proper authentication tokens
            if not access_token:
                flash('Authentication failed: No access token received', 'error')
                return render_template('login.html')
            
            # Additional validation - check token format (basic length check)
            if len(access_token) < 20:  # Basic validation
                flash('Authentication failed: Invalid access token format', 'error')
                return render_template('login.html')

            # Store in session with expiration
            session['authenticated'] = True
            session['access_token'] = access_token
            session['session_token'] = session_token or 'default_session'
            session['sid'] = sid or 'default_sid'
            session['ucc'] = ucc
            session['client'] = client
            # Convert to IST (UTC+5:30)
            ist_time = datetime.now() + timedelta(hours=5, minutes=30)
            session['login_time'] = ist_time.strftime('%B %d, %Y at %I:%M:%S %p IST')
            session['greeting_name'] = session_data.get('greetingName') or session_data.get('greeting_name') or ucc
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
                # Check if it's a TOTP or MPIN specific error
                msg = result.get("message")
                logging.error(f"Authentication failed with message: {msg}")
                
                if 'totp' in msg.lower() or 'authenticator' in msg.lower():
                    error_message = f'TOTP Error: {msg}'
                elif 'mpin' in msg.lower():
                    error_message = f'MPIN Error: {msg}'
                elif 'invalid credentials' in msg.lower():
                    error_message = 'Invalid credentials. Please check your TOTP and MPIN.'
                else:
                    error_message = f'Authentication failed: {msg}'
            elif not result:
                error_message = "Authentication failed: No response from server"
                logging.error("No result returned from authentication")
            else:
                logging.error(f"Authentication failed with result: {result}")
                
            flash(error_message, 'error')
            return render_template('login.html')

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash(f'Login failed: {str(e)}', 'error')
        return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout and clear session completely"""
    try:
        # Get current session info for logging
        ucc = session.get('ucc', 'Unknown')
        
        # Clear Flask session using utility function
        clear_session()
        
        # Also clear any potential cached client data
        if 'client' in session:
            try:
                client = session.get('client')
                if client and hasattr(client, 'logout'):
                    client.logout()
            except Exception as logout_error:
                logging.warning(f"Error during client logout: {logout_error}")
        
        # Force complete session invalidation
        session.clear()
        session.permanent = False
        
        # Also try to clear any server-side session data if using file sessions
        try:
            from flask import request
            if hasattr(request, 'session'):
                request.session.clear()
        except:
            pass
        
        flash('Successfully logged out', 'success')
        logging.info(f"User {ucc} logged out successfully")
        
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        # Even if there's an error, force clear the session
        try:
            session.clear()
            session.permanent = False
        except:
            pass
        flash('Logged out with warnings', 'warning')
    
    return redirect(url_for('auth.login'))