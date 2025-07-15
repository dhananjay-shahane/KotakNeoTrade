"""
Apply email functionality to the registration process.
"""
import os
from flask import Flask, render_template, redirect, url_for

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "demo-secret-key-2025")

@app.route('/')
def index():
    """Home page - redirect to portfolio"""
    return redirect(url_for('portfolio'))

@app.route('/portfolio')
def portfolio():
    """Portfolio page"""
    return render_template('portfolio.html')

@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page"""
    return render_template('trading_signals.html')

@app.route('/deals')
def deals():
    """Deals page"""
    return render_template('deals.html')

@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page"""
    return render_template('base.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

The provided original code focuses on setting up a basic Flask application with routing and template rendering. However, the user's request is about implementing email notifications upon successful user registration, which involves database interaction, user authentication, and email sending. The original code lacks all these functionalities.  Given that the changes provided also relate to a more complete application structure, I will provide the likely complete code including user registration and email sending.

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import string
import os

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "demo-secret-key-2025")

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/trading_platform.db'  # Ensure 'instance' folder exists
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your-app-password'     # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'


# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_registration_email(user_email, username, password):
    """Send registration confirmation email with credentials"""
    try:
        msg = Message(
            subject="Welcome to Trading Platform - Your Account Details",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )

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
                .steps {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .step {{
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 4px solid #007bff;
                    background: #f8f9fa;
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
                <p>Congratulations! Your trading platform account has been successfully registered. Below are your login credentials:</p>

                <div class="credentials-box">
                    <h3>🔐 Your Login Credentials</h3>
                    <div class="credential-item">
                        <span class="credential-label">Username:</span>
                        <span class="credential-value">{username}</span>
                    </div>
                    <div class="credential-item">
                        <span class="credential-label">Password:</span>
                        <span class="credential-value">{password}</span>
                    </div>
                    <div class="credential-item">
                        <span class="credential-label">Email:</span>
                        <span class="credential-value">{user_email}</span>
                    </div>
                </div>

                <div class="warning">
                    <strong>⚠️ Important Security Notice:</strong><br>
                    Please keep these credentials safe and secure. We recommend changing your password after your first login for enhanced security.
                </div>

                <div class="steps">
                    <h3>📋 Next Steps:</h3>
                    <div class="step">
                        <strong>Step 1:</strong> Log in to your account using the credentials above
                    </div>
                    <div class="step">
                        <strong>Step 2:</strong> Complete your profile setup
                    </div>
                    <div class="step">
                        <strong>Step 3:</strong> Start exploring our trading features
                    </div>
                    <div class="step">
                        <strong>Step 4:</strong> Consider changing your password for better security
                    </div>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/login" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Login to Your Account</a>
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

        Next Steps:
        1. Log in to your account using the credentials above
        2. Complete your profile setup
        3. Start exploring our trading features
        4. Consider changing your password for better security

        Thank you for choosing Trading Platform!
        """

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Define routes
@app.route('/')
def index():
    """Home page - redirect to portfolio"""
    return redirect(url_for('portfolio'))

@app.route('/portfolio')
def portfolio():
    """Portfolio page"""
    return render_template('portfolio.html')

@app.route('/trading-signals')
def trading_signals():
    """Trading Signals page"""
    return render_template('trading_signals.html')

@app.route('/deals')
def deals():
    """Deals page"""
    return render_template('deals.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate input (add more robust validation)
        if not all([email, mobile, username, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        # Check if user already exists (add more robust checks)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.', 'error')
            return render_template('auth/register.html')

        # Create new user
        user = User(
            email=email,
            mobile=mobile,
            username=username
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()

            # Send registration email with credentials
            email_sent = send_registration_email(email, username, password)

            if email_sent:
                flash('Registration successful! Please check your email for login credentials.', 'success')
            else:
                flash('Registration successful! However, we couldn\'t send the confirmation email. Please note your credentials.', 'warning')

            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('portfolio'))  # Redirect to a logged-in area
        else:
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 error page"""
    return render_template('base.html'), 404

# Create database tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == '__main__':
    # Ensure the instance folder exists
    os.makedirs(os.path.dirname('instance/trading_platform.db'), exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)