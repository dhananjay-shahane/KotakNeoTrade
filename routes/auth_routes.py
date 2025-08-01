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
                email_sent = send_user_id_email(user_found)
                if email_sent:
                    logging.info(f"User ID email sent successfully for: {contact_info[:3]}***")
                else:
                    logging.error(f"Failed to send User ID email for: {contact_info[:3]}***")
            else:
                logging.info(f"No user found for contact info: {contact_info[:3]}***")
            
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
    try:
        # Use centralized database configuration
        from config.database_config import execute_db_query
        
        # First check if user exists by email
        result = execute_db_query("SELECT username, email, mobile FROM external_users WHERE email = %s LIMIT 1", (contact_info,))
        
        # If not found by email, check by mobile
        if not result or len(result) == 0:
            result = execute_db_query("SELECT username, email, mobile FROM external_users WHERE mobile = %s LIMIT 1", (contact_info,))
        
        if result and len(result) > 0:
            user_data = {
                'username': result[0]['username'],
                'email': result[0]['email'], 
                'mobile': result[0]['mobile']
            }
            logging.info(f"User found in database: {user_data['username']}")
            return user_data
        else:
            logging.info(f"No user found for contact: {contact_info[:3]}***")
            return None
        
    except Exception as e:
        logging.error(f"Database error in check_user_exists_by_contact: {str(e)}")
        return None


def send_user_id_email(user_data):
    """Send email with user ID to the registered email address using direct SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os
        
        # Email configuration
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        email_user = 'dhanushahane01@gmail.com'
        email_password = 'sljo pinu ajrh padp'
        
        logging.info(f"Attempting to send User ID email to: {user_data['email']}")
        logging.info(f"SMTP Configuration - Server: {smtp_server}, Port: {smtp_port}")
        logging.info(f"Email user: {email_user}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = user_data['email']
        msg['Subject'] = 'Your Trading Platform User ID'
        
        # Create HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Trading Platform User ID</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Trading Platform</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0; font-size: 16px;">Your User ID Request</p>
            </div>
            
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-bottom: 20px;">Dear Valued User,</h2>
                
                <p style="font-size: 16px; margin-bottom: 20px;">You requested to retrieve your User ID for the Trading Platform. Here are your account details:</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <h3 style="color: #667eea; margin: 0 0 15px 0;">Your Account Information</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">User ID:</td>
                            <td style="padding: 8px 0; color: #333; font-weight: bold; font-size: 18px;">{user_data['username']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Registered Email:</td>
                            <td style="padding: 8px 0; color: #333;">{user_data['email']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #555;">Registered Mobile:</td>
                            <td style="padding: 8px 0; color: #333;">{user_data['mobile']}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #e8f4fd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0; color: #0c5460;"><strong>How to Login:</strong> Use your User ID along with your password to access your trading account.</p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <p style="margin: 0; color: #856404;"><strong>Security Notice:</strong> If you did not request this information, please ignore this email and ensure your account is secure.</p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; color: #666; font-size: 14px;">For assistance, contact our support team</p>
                <p style="margin: 5px 0 0; color: #666; font-size: 14px;">Best regards,<br><strong>Trading Platform Support Team</strong></p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_body = f"""Dear User,

You requested to retrieve your User ID for the Trading Platform.

Your Account Information:
• User ID: {user_data['username']}
• Registered Email: {user_data['email']}  
• Registered Mobile: {user_data['mobile']}

How to Login: Use your User ID along with your password to access your trading account.

Security Notice: If you did not request this information, please ignore this email.

For assistance, contact our support team.

Best regards,
Trading Platform Support Team"""
        
        # Attach both HTML and plain text versions
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email using SMTP
        logging.info("Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        logging.info("Starting TLS...")
        server.starttls()
        logging.info("Logging in to SMTP server...")
        server.login(email_user, email_password)
        logging.info("Sending email message...")
        text = msg.as_string()
        server.sendmail(email_user, user_data['email'], text)
        server.quit()
        
        logging.info(f"✅ User ID email sent successfully to: {user_data['email']}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"❌ SMTP Authentication failed: {str(e)}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logging.error(f"❌ SMTP Recipients refused: {str(e)}")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"❌ SMTP Server disconnected: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"❌ Failed to send user ID email: {str(e)}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return False
