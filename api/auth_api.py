"""
Fixed Authentication API for user login and registration functionality
"""
import os
import string
import psycopg2
import sys
from datetime import datetime
from flask import request, flash, redirect, url_for, render_template, jsonify
from flask_login import login_user, logout_user, current_user
from flask_mail import Mail, Message
from models import db, User
import secrets

# Add scripts to path for dynamic deals service
sys.path.append('scripts')
from scripts.dynamic_user_deals import DynamicUserDealsService

# Initialize dynamic deals service
dynamic_deals_service = DynamicUserDealsService()


def get_external_db_connection():
    """Get connection to external PostgreSQL database using centralized config"""
    try:
        sys.path.append('.')
        from config.database_config import get_db_connection
        conn = get_db_connection()
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
        
        # Check if user already exists
        cursor.execute('''
            SELECT username FROM external_users WHERE email = %s OR username = %s
        ''', (email, username))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            print(f"User with email {email} or username {username} already exists")
            return False
        
        # Insert user data
        cursor.execute('''
            INSERT INTO external_users (username, password, email, mobile, trading_account_name)
            VALUES (%s, %s, %s, %s, %s)
        ''', (username, password, email, mobile, trading_account_name or 'Not Set'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"User {username} successfully stored in external database")
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


# Email configuration - moved from main app
class EmailService:
    """Email service for sending registration confirmations"""

    @staticmethod
    def configure_mail(app):
        """Configure Flask-Mail with app"""
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or os.environ.get('EMAIL_USER')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or os.environ.get('EMAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or app.config['MAIL_USERNAME']

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

        if not mail.app.config.get('MAIL_USERNAME') or not mail.app.config.get('MAIL_PASSWORD'):
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

            # Beautiful email template matching the design
            msg.html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to Trading Platform</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f8f9fa;
                        line-height: 1.6;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .header p {{
                        margin: 10px 0 0 0;
                        font-size: 16px;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .greeting {{
                        font-size: 18px;
                        font-weight: 600;
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    .message {{
                        color: #666;
                        margin-bottom: 30px;
                    }}
                    .credentials-section {{
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        padding: 25px;
                        margin: 20px 0;
                        border-left: 4px solid #667eea;
                    }}
                    .credentials-title {{
                        font-size: 16px;
                        font-weight: 600;
                        color: #333;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                    }}
                    .credentials-subtitle {{
                        font-size: 14px;
                        color: #666;
                        margin-bottom: 20px;
                    }}
                    .credential-item {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 10px 0;
                        border-bottom: 1px solid #e9ecef;
                    }}
                    .credential-item:last-child {{
                        border-bottom: none;
                    }}
                    .credential-label {{
                        font-weight: 500;
                        color: #333;
                    }}
                    .credential-value {{
                        color: #667eea;
                        font-weight: 600;
                        font-family: monospace;
                        background-color: #e3f2fd;
                        padding: 4px 8px;
                        border-radius: 4px;
                    }}
                    .security-notice {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 6px;
                        padding: 15px;
                        margin-top: 25px;
                    }}
                    .security-title {{
                        font-weight: 600;
                        color: #856404;
                        margin-bottom: 5px;
                    }}
                    .security-text {{
                        color: #856404;
                        font-size: 14px;
                        margin: 0;
                    }}
                    .footer {{
                        padding: 20px 30px;
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                        border-top: 1px solid #e9ecef;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>📈 Trading Platform</h1>
                        <p>Welcome to Our Trading Platform!</p>
                        <p style="font-size: 14px; margin-top: 15px;">Your account has been successfully created</p>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">Hello {username.upper()}!</div>
                        <div class="message">
                            Congratulations! Your trading platform account has been successfully registered.<br><br>
                            <strong>IMPORTANT:</strong> Below are your login credentials. Please store them securely as you will need them to access your account.
                        </div>
                        
                        <div class="credentials-section">
                            <div class="credentials-title">🔐 Your Login Credentials</div>
                            <div class="credentials-subtitle">Use these credentials to login to the trading platform:</div>
                            
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
                        
                        <div class="security-notice">
                            <div class="security-title">⚠️ Important Security Notice:</div>
                            <p class="security-text">Please keep these credentials safe and secure. We recommend changing your password after your first login for enhanced security.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 Trading Platform. All rights reserved.</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text version
            msg.body = f"""
            Welcome to Trading Platform!

            Login Credentials:
            Username: {username}
            Password: {password}
            Email: {user_email}

            Please keep these credentials safe and secure.
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
        username = request.form.get('email', '').strip()  # Form field is named 'email' but contains username
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
                # Create user in local database from external data - FIXED
                user = User()
                user.username = username
                user.email = external_user['email']
                user.mobile = external_user['mobile']
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            flash('Login successful! Welcome to the trading platform.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('portfolio'))
        else:
            # Fallback to local database authentication
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful! Welcome to the trading platform.', 'success')
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

        # Generate 5-letter username from email + mobile combination
        try:
            # Extract first 3 letters from email (before @)
            email_part = email.split('@')[0][:3].lower()
            # Extract last 2 digits from mobile
            mobile_digits = ''.join(filter(str.isdigit, mobile))[-2:]
            username = email_part + mobile_digits
            
            # Ensure username is exactly 5 characters
            if len(username) < 5:
                username = username.ljust(5, '0')
            username = username[:5]

            # Store user details in external database
            if store_user_in_external_db(username, password, email, mobile):
                # Create user-specific deals table
                if dynamic_deals_service.create_user_deals_table(username):
                    print(f"✅ Created deals table for user: {username}")
                else:
                    print(f"⚠️ Failed to create deals table for user: {username}")
                
                # Send registration email if email service is configured
                if mail:
                    EmailService.send_registration_email(mail, email, username, password)

                flash('Registration successful! Please check your email for login credentials. Do not close this message until you have received the email.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Email might already be registered.', 'error')
                return render_template('auth/register.html')

        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')

    return render_template('auth/register.html')


def handle_logout():
    """Handle user logout"""
    logout_user()
    from flask import session
    session.pop('_flashes', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))