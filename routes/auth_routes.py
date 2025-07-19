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
    """Kotak Neo login page with TOTP authentication"""
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
                    # Store in Flask session (only serializable data)
                    session['authenticated'] = True
                    session['access_token'] = session_data.get('access_token')
                    session['session_token'] = session_data.get('session_token')
                    session['sid'] = session_data.get('sid')
                    session['ucc'] = ucc
                    session['mobile_number'] = mobile_number
                    session['greeting_name'] = session_data.get('greetingName', ucc)
                    session['user_id'] = session_data.get('user_id', ucc)
                    session['client_code'] = session_data.get('client_code')
                    session['kotak_logged_in'] = True
                    session['login_type'] = 'kotak_neo'
                    session['client'] = client  # Store the client object for API calls
                    session.permanent = True
                    
                    # Note: Client object stored for trading functionality

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

                    # Store user data in database (optional - login still works without DB)
                    try:
                        from Scripts.user_manager import UserManager
                        user_manager = UserManager()
                        db_user = user_manager.create_or_update_user(login_response)
                        user_session = user_manager.create_user_session(db_user.id, login_response)
                        
                        session['db_user_id'] = db_user.id
                        session['db_session_id'] = user_session.session_id
                        
                        logging.info(f"User data stored in database for UCC: {ucc}")
                    except Exception as db_error:
                        logging.warning(f"Database storage skipped: {db_error}")
                        # Continue with login even if DB storage fails

                    # Store essential session data for sidebar and header
                    session['ucc'] = ucc
                    session['greeting_name'] = session_data.get('greetingName', '')
                    session['mobile_number'] = mobile_number
                    session['kotak_logged_in'] = True  # Flag for sidebar visibility
                    session['authenticated'] = True  # General authentication flag
                    
                    flash('Successfully authenticated with TOTP!', 'success')
                    logging.info(f"Login successful for UCC: {ucc}, redirecting to dashboard")
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


@auth_bp.route('/trading-account/login', methods=['GET', 'POST'])
def trading_account_login():
    """Default trading account login using auth folder templates"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('email', '').strip()  # Form uses 'email' field for username
            password = request.form.get('password', '').strip()

            # Validate inputs
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('auth/login.html')

            # For demo purposes, create a simple authentication
            # In production, this would validate against your user database
            if username and password:
                # Store user session with all required fields
                session['authenticated'] = True
                session['username'] = username
                session['user_id'] = username  # Use username as user ID for header display
                session['login_type'] = 'trading_account'
                session['access_token'] = 'demo_token_' + username  # Demo token for validation
                session['ucc'] = username  # Use username as UCC for trading account
                session['greeting_name'] = username
                session['kotak_logged_in'] = True  # Mark as logged in to prevent repeated prompts
                session.permanent = True
                
                logging.info(f"Trading account login successful for: {username}")
                flash('Login successful!', 'success')
                
                # Redirect to dashboard
                return redirect(url_for('main_routes.dashboard'))
            else:
                flash('Invalid username or password', 'error')

        except Exception as e:
            logging.error(f"Trading account login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')

    # Redirect authenticated users to dashboard
    if validate_current_session():
        return redirect(url_for('main_routes.dashboard'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    # Clear all session data
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth_routes.trading_account_login'))