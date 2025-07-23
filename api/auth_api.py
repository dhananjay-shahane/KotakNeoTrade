"""
Authentication API for user login and registration functionality
"""
import os
from flask import request, flash, redirect, url_for, render_template, jsonify
from flask_login import login_user, logout_user, current_user
from flask_mail import Mail, Message
from models import db, User
import secrets


def get_external_db_connection():
    """Get connection to external PostgreSQL database"""
    try:
        import psycopg2
        db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"Error connecting to external database: {e}")
        return None


def create_external_users_table():
    """Create external_users table if it doesn't exist"""
    conn = get_external_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_users (
                sr SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(120) NOT NULL UNIQUE,
                mobile VARCHAR(15) NOT NULL,
                trading_account_name VARCHAR(100),
                datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating external_users table: {e}")
        return False


def store_user_in_external_db(username, password, email, mobile, trading_account_name=None):
    """Store user registration details in external PostgreSQL database"""
    try:
        # Ensure table exists
        create_external_users_table()
        
        conn = get_external_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Insert user data
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO external_users (username, password, email, mobile, trading_account_name, datetime)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (username, password, email, mobile, trading_account_name or 'Not Set', current_datetime))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error storing user in external database: {e}")
        return False


def authenticate_user_from_external_db(username, password):
    """Authenticate user from external PostgreSQL database"""
    try:
        conn = get_external_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sr, username, email, mobile, trading_account_name, datetime 
            FROM external_users 
            WHERE username = %s AND password = %s
        ''', (username, password))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'sr': result[0],
                'username': result[1],
                'email': result[2],
                'mobile': result[3],
                'trading_account_name': result[4],
                'datetime': result[5]
            }
        
        return None
        
    except Exception as e:
        print(f"Error authenticating user from external database: {e}")
        return None


import string
import psycopg2
from datetime import datetime


# Email configuration - moved from main app
class EmailService:
    """Email service for sending registration confirmations"""

    @staticmethod
    def configure_mail(app):
        """Configure Flask-Mail with app"""
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

        # Only configure mail if credentials are provided
        if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
            print("❌ Email credentials not configured. Set MAIL_USERNAME and MAIL_PASSWORD in Secrets.")
            print("📧 Email service will be disabled.")
            return None

        print(f"✅ Email service configured for: {app.config['MAIL_USERNAME']}")
        return Mail(app)

    @staticmethod
    def send_registration_email(mail, user_email, username, password):
        """Send registration confirmation email with credentials"""
        if not mail:
            print("Email service not configured, skipping email send")
            return False

        if not mail.app.config.get('MAIL_USERNAME') or not mail.app.config.get(
                'MAIL_PASSWORD'):
            print("Email credentials not configured, skipping email send")
            return False

        try:
            print(f"Attempting to send registration email to: {user_email}")
            print(f"Using SMTP server: {mail.app.config.get('MAIL_SERVER')}")
            print(f"Sending credentials for username: {username}")

            msg = Message(
                subject="Welcome to Trading Platform - Your Account Details",
                sender=mail.app.config.get('MAIL_DEFAULT_SENDER') or mail.app.config.get('MAIL_USERNAME'),
                recipients=[user_email])

            # Email HTML template
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to Trading Platform</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f8f9fa;
                        padding: 30px;
                        border-radius: 0 0 10px 10px;
                    }}
                    .credentials-box {{
                        background: white;
                        border: 2px solid #e9ecef;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .credential-item {{
                        margin: 15px 0;
                        padding: 10px;
                        background: #f8f9fa;
                        border-radius: 5px;
                    }}
                    .credential-label {{
                        font-weight: bold;
                        color: #495057;
                        display: block;
                        margin-bottom: 5px;
                    }}
                    .credential-value {{
                        font-size: 18px;
                        color: #007bff;
                        font-weight: bold;
                        font-family: monospace;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        color: #856404;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        color: #6c757d;
                        font-size: 14px;
                    }}
                    .logo {{
                        font-size: 24px;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="logo">📈 Trading Platform</div>
                    <h1>Welcome to Our Trading Platform!</h1>
                    <p>Your account has been successfully created</p>
                </div>

                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Congratulations! Your trading platform account has been successfully registered.</p>
                    
                    <p><strong>IMPORTANT:</strong> Below are your login credentials. Please save them securely as you will need them to access your account.</p>

                    <div class="credentials-box">
                        <h3>🔐 Your Login Credentials</h3>
                        <p><strong>Use these credentials to login to the trading platform:</strong></p>
                        <div class="credential-item">
                            <span class="credential-label">Username:</span>
                            <span class="credential-value">{username}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Password:</span>
                            <span class="credential-value">{password}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Registered Email:</span>
                            <span class="credential-value">{user_email}</span>
                        </div>
                    </div>

                    <div class="warning">
                        <strong>⚠️ Important Security Notice:</strong><br>
                        Please keep these credentials safe and secure. We recommend changing your password after your first login for enhanced security.
                    </div>
                </div>

                <div class="footer">
                    <p>Thank you for choosing Trading Platform!</p>
                    <p>If you have any questions, please contact our support team.</p>
                    <p style="font-size: 12px; color: #adb5bd;">This is an automated email. Please do not reply directly to this message.</p>
                </div>
            </body>
            </html>
            """

            # Plain text version
            msg.body = f"""
            Welcome to Trading Platform!

            Your account has been successfully created.

            Login Credentials:
            Username: {username}
            Password: {password}
            Email: {user_email}

            Please keep these credentials safe and secure.

            Thank you for choosing Trading Platform!
            """

            mail.send(msg)
            print(f"Email sent successfully to {user_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            import traceback
            traceback.print_exc()
            return False


def handle_login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('portfolio'))

    if request.method == 'POST':
        username = request.form.get(
            'email',
            '').strip()  # Form field is named 'email' but contains username
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')

        # First try to authenticate from external database
        external_user = authenticate_user_from_external_db(username, password)
        
        if external_user:
            # Check if user exists in local database, if not create one
            user = User.query.filter_by(username=username).first()
            if not user:
                # Create user in local database from external data
                user = User(
                    username=username,
                    email=external_user['email'],
                    mobile=external_user['mobile']
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('portfolio'))
        else:
            # Fallback to local database authentication
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('portfolio'))
            else:
                flash('Invalid username or password', 'error')

    return render_template('auth/login.html')


def handle_register(mail=None):
    """Handle user registration with optional email service"""
    if current_user.is_authenticated:
        return redirect(url_for('portfolio'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validate inputs
        if not all([email, mobile, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register.html')

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile number already registered', 'error')
            return render_template('auth/register.html')

        # Create new user
        try:
            # Generate 5-letter username from email + mobile combination
            username = User.generate_username(email, mobile)

            user = User(email=email, mobile=mobile, username=username)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            # Send registration email if email service is configured
            email_sent = False
            if mail:
                email_sent = EmailService.send_registration_email(
                    mail, email, username, password)

            # Store user details in external database
            try:
                store_user_in_external_db(username, password, email, mobile)
                print(f"User {username} stored in external database successfully")
            except Exception as e:
                print(f"Failed to store user in external database: {e}")

            # Always show email check message regardless of email service status
            flash(
                'Registration successful! Please check your email inbox for your username and password details.',
                'success')
            flash(
                'Use the credentials from your email to login to your account.',
                'info')

            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")

    return render_template('auth/register.html')


def handle_logout():
    """Handle user logout"""
    logout_user()
    # Clear all flash messages to prevent showing registration messages after logout
    from flask import session
    session.pop('_flashes', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


# API endpoints for AJAX requests
def login_api():
    """API endpoint for login via AJAX"""
    try:
        data = request.get_json()
        username = data.get(
            'email',
            '').strip()  # Form field named 'email' but contains username
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400

        # First try to authenticate from external database
        external_user = authenticate_user_from_external_db(username, password)
        
        if external_user:
            # Check if user exists in local database, if not create one
            user = User.query.filter_by(username=username).first()
            if not user:
                # Create user in local database from external data
                user = User(
                    username=username,
                    email=external_user['email'],
                    mobile=external_user['mobile']
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            return jsonify({
                'success': True,
                'message': f'Welcome back, {user.username}!',
                'redirect_url': url_for('portfolio')
            })
        else:
            # Fallback to local database authentication
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return jsonify({
                    'success': True,
                    'message': f'Welcome back, {user.username}!',
                    'redirect_url': url_for('portfolio')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password'
                }), 401

    except Exception as e:
        print(f"Login API error: {e}")
        return jsonify({
            'success': False,
            'message': 'Login failed. Please try again.'
        }), 500


def register_api(mail=None):
    """API endpoint for registration via AJAX"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        mobile = data.get('mobile', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()

        # Validate inputs
        if not all([email, mobile, password, confirm_password]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400

        if password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success':
                False,
                'message':
                'Password must be at least 6 characters long'
            }), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409

        if User.query.filter_by(mobile=mobile).first():
            return jsonify({
                'success': False,
                'message': 'Mobile number already registered'
            }), 409

        # Create new user with 5-letter username from email + mobile combination
        username = User.generate_username(email, mobile)

        user = User(email=email, mobile=mobile, username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Send registration email if email service is configured
        email_sent = False
        if mail:
            email_sent = EmailService.send_registration_email(
                mail, email, username, password)

        # Store user details in external database
        try:
            store_user_in_external_db(username, password, email, mobile)
            print(f"User {username} stored in external database successfully")
        except Exception as e:
            print(f"Failed to store user in external database: {e}")

        # Always show email check message regardless of email service status
        message = 'Registration successful! Please check your email inbox for your username and password details.'

        return jsonify({
            'success': True,
            'message': message,
            'username': username,
            'redirect_url': url_for('login')
        })

    except Exception as e:
        db.session.rollback()
        print(f"Registration API error: {e}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }), 500


def check_user_status():
    """API endpoint to check if user is authenticated"""
    return jsonify({
        'authenticated':
        current_user.is_authenticated,
        'username':
        current_user.username if current_user.is_authenticated else None
    })
