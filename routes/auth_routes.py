"""
Authentication routes for Kotak Neo Trading Platform
Handles login, logout, and authentication-related pages
"""
import logging
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from core.auth import login_user, logout_user, validate_current_session
from Scripts.neo_client import NeoClient
from Scripts.user_manager import UserManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env', override=True)

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
            result = neo_client.execute_totp_login(mobile_number, ucc, totp,
                                                   mpin)

            if result and result.get('success'):
                client = result.get('client')
                session_data = result.get('session_data', {})

                if client:
                    # Store in Flask session (only serializable data)
                    session['authenticated'] = True
                    session['access_token'] = session_data.get('access_token')
                    session['session_token'] = session_data.get(
                        'session_token')
                    session['sid'] = session_data.get('sid')
                    session['ucc'] = ucc
                    session['mobile_number'] = mobile_number
                    session['greeting_name'] = session_data.get(
                        'greetingName', ucc)
                    session['user_id'] = session_data.get('user_id', ucc)
                    session['client_code'] = session_data.get('client_code')
                    session['kotak_logged_in'] = True
                    session['login_type'] = 'kotak_neo'
                    session[
                        'client'] = client  # Store the client object for API calls
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
                        db_user = user_manager.create_or_update_user(
                            login_response)
                        user_session = user_manager.create_user_session(
                            db_user.id, login_response)

                        session['db_user_id'] = db_user.id
                        session['db_session_id'] = user_session.session_id

                        logging.info(
                            f"User data stored in database for UCC: {ucc}")
                    except Exception as db_error:
                        logging.warning(
                            f"Database storage skipped: {db_error}")
                        # Continue with login even if DB storage fails

                    # Store essential session data for sidebar and header
                    session['ucc'] = ucc
                    session['greeting_name'] = session_data.get(
                        'greetingName', '')
                    session['mobile_number'] = mobile_number
                    session[
                        'kotak_logged_in'] = True  # Flag for sidebar visibility
                    session[
                        'authenticated'] = True  # General authentication flag

                    # Clear any existing flash messages to prevent conflicts
                    session.pop('_flashes', None)
                    flash('Successfully authenticated with TOTP!', 'success')
                    logging.info(
                        f"Login successful for UCC: {ucc}, redirecting to dashboard"
                    )
                    return redirect(url_for('main_routes.dashboard'))
                else:
                    flash('Invalid client data received', 'error')
            else:
                error_msg = result.get(
                    'message',
                    'Authentication failed') if result else 'Login failed'
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
            username = request.form.get(
                'username', '').strip()  # Form uses 'username' field
            password = request.form.get('password', '').strip()

            # Validate inputs
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('auth/login.html')

            # Authenticate against external PostgreSQL database
            user_data = authenticate_external_user(username, password)
            if user_data:
                # Store user session with all required fields for dashboard access
                session['authenticated'] = True
                session['username'] = user_data['username']
                session['user_id'] = user_data['sr']  # User ID from database
                session['email'] = user_data['email']  # User email
                session['mobile'] = user_data['mobile']  # User mobile
                session['login_time'] = user_data['login_time'].strftime(
                    '%Y-%m-%d %H:%M:%S'
                ) if user_data['login_time'] else 'Unknown'
                session['trading_account_name'] = user_data[
                    'trading_account_name']
                session['login_type'] = 'trading_account'
                session[
                    'access_token'] = 'token_' + username  # Token for validation
                session['ucc'] = username  # Required field for dashboard
                session['greeting_name'] = username  # Display name
                # Don't set kotak_logged_in for trading account login
                session.permanent = True

                logging.info(
                    f"Trading account login successful for: {username}")
                flash('Login successful!', 'success')

                # Redirect to portfolio instead of dashboard
                return redirect(url_for('portfolio'))
            else:
                flash('Invalid username or password', 'error')

        except Exception as e:
            logging.error(f"Trading account login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')

    # Redirect authenticated users to portfolio
    if validate_current_session():
        return redirect(url_for('portfolio'))

    return render_template('auth/login.html')


def authenticate_external_user(username, password):
    """Authenticate user against PostgreSQL database and return user data"""
    import psycopg2
    import os
    from urllib.parse import urlparse

    try:
        # Use DATABASE_URL from Replit environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logging.error("DATABASE_URL not found")
            return None

        # Parse the DATABASE_URL
        url = urlparse(database_url)
        db_config = {
            'host': url.hostname,
            'database': url.path[1:],  # Remove leading slash
            'user': url.username,
            'password': url.password,
            'port': url.port or 5432
        }

        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Get full user details from external_users table
        cursor.execute(
            """
            SELECT sr, username, email, mobile, trading_account_name, datetime 
            FROM external_users 
            WHERE username = %s AND password = %s
        """, (username, password))

        result = cursor.fetchone()

        # Close connection
        cursor.close()
        conn.close()

        # Return user data if found, None otherwise
        if result:
            return {
                'sr': result[0],
                'username': result[1],
                'email': result[2],
                'mobile': result[3],
                'trading_account_name': result[4],
                'login_time': result[5]
            }
        return None

    except Exception as e:
        logging.error(f"Database authentication error: {str(e)}")
        return None


@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    # Clear all session data
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth_routes.trading_account_login'))


@auth_bp.route('/logout-kotak')
def logout_kotak():
    """Logout only from Kotak account while keeping trading account session"""
    # Clear only Kotak-specific session data but preserve trading account data
    kotak_keys = ['kotak_logged_in', 'client', 'mobile_number', 'mpin', 'totp']
    for key in kotak_keys:
        session.pop(key, None)

    # If this was a Kotak login, preserve the UCC for trading account functionality
    if session.get('login_type') == 'kotak_neo':
        session['login_type'] = 'trading_account'

    # Clear any existing flash messages before adding logout message
    session.pop('_flashes', None)
    flash('Logged out from Kotak Neo successfully', 'info')
    return redirect(url_for('portfolio'))


@auth_bp.route('/know-user-id', methods=['GET', 'POST'])
def know_user_id():
    """Know My User ID functionality - Enter mobile number or email to retrieve User ID"""
    if request.method == 'POST':
        try:
            # Get contact info from form (mobile number or email)
            contact_info = request.form.get('contact_info', '').strip()
            
            if not contact_info:
                flash('Please enter your mobile number or email address', 'error')
                return render_template('auth/know_user_id.html')
            
            # Log the attempt for security auditing
            logging.info(f"User ID retrieval requested for: {contact_info[:3]}***")
            
            # Check if the contact info exists in external_users table
            user_found = check_user_exists_by_contact(contact_info)
            
            if user_found:
                # Send email with user ID to the registered email address
                send_user_id_email(user_found)
                logging.info(f"User ID email sent for: {contact_info[:3]}***")
            
            # Always show the same neutral message regardless of whether user exists
            flash(
                'If the account exists, the admin will send you an email containing your user ID at your registered email address.',
                'info'
            )
            
            return render_template('auth/know_user_id.html')
            
        except Exception as e:
            logging.error(f"Know User ID error: {str(e)}")
            flash('An error occurred. Please try again later.', 'error')
            return render_template('auth/know_user_id.html')
    
    return render_template('auth/know_user_id.html')


def check_user_exists_by_contact(contact_info):
    """Check if user exists by mobile number or email and return user data"""
    from config.database_config import get_db_dict_connection
    
    try:
        conn = get_db_dict_connection()
        if not conn:
            logging.error("Database connection failed")
            return None
            
        with conn.cursor() as cursor:
            # Check both email and mobile fields
            cursor.execute(
                """
                SELECT username, email, mobile_number 
                FROM external_users 
                WHERE email = %s OR mobile_number = %s
                LIMIT 1
                """, (contact_info, contact_info)
            )
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'username': result['username'],
                    'email': result['email'],
                    'mobile_number': result['mobile_number']
                }
                
        conn.close()
        return None
        
    except Exception as e:
        logging.error(f"Database error in check_user_exists_by_contact: {str(e)}")
        return None


def send_user_id_email(user_data):
    """Send email with user ID to the registered email address"""
    try:
        from flask_mail import Mail, Message
        from flask import current_app
        
        # Configure Flask-Mail if not already configured
        if not hasattr(current_app, 'mail'):
            from flask_mail import Mail
            mail = Mail(current_app)
        else:
            mail = current_app.mail
        
        # Create email message
        msg = Message(
            subject='Your Trading Platform User ID',
            sender=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@trading-platform.com'),
            recipients=[user_data['email']]
        )
        
        # Email content
        msg.body = f"""
Dear User,

You requested to retrieve your User ID for the Trading Platform.

Your User ID: {user_data['username']}

Please use this User ID along with your password to login to your trading account.

If you did not request this information, please ignore this email.

For any assistance, please contact our support team.

Best regards,
Trading Platform Support Team
        """
        
        msg.html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; margin: 0;">Trading Platform - User ID Retrieval</h2>
    </div>
    
    <div style="background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">
        <p>Dear User,</p>
        
        <p>You requested to retrieve your User ID for the Trading Platform.</p>
        
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin: 0; color: #1976d2;">Your User ID: <strong>{user_data['username']}</strong></h3>
        </div>
        
        <p>Please use this User ID along with your password to login to your trading account.</p>
        
        <p style="color: #6c757d; font-size: 14px;">
            <strong>Security Note:</strong> If you did not request this information, please ignore this email.
        </p>
        
        <hr style="border: none; border-top: 1px solid #e9ecef; margin: 20px 0;">
        
        <p style="color: #6c757d; font-size: 14px;">
            For any assistance, please contact our support team.<br>
            Best regards,<br>
            Trading Platform Support Team
        </p>
    </div>
</body>
</html>
        """
        
        # Send email
        mail.send(msg)
        logging.info(f"User ID email sent successfully to: {user_data['email'][:3]}***")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send User ID email: {str(e)}")
        return False
