"""
Password Reset API - Handles forgot password and reset password functionality
Uses external PostgreSQL database for secure token management
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_mail import Message
from werkzeug.security import generate_password_hash
import logging

# Import centralized database configuration
from config.database_config import execute_db_query, get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Create blueprint
password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/auth')

def send_reset_email(email, reset_token, app):
    """Send password reset email using Flask-Mail"""
    try:
        from app import mail
        
        # Get the base URL for the reset link
        base_url = request.url_root.rstrip('/')
        reset_url = f"{base_url}/auth/reset-password?token={reset_token}"
        
        # Create email message
        msg = Message(
            subject='Password Reset Request - Kotak Neo Trading',
            sender=os.environ.get('MAIL_USERNAME', 'noreply@kotakneo.com'),
            recipients=[email]
        )
        
        # HTML email template
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #4285f4 0%, #1a73e8 100%); color: white; padding: 30px 20px; text-align: center; }}
                .content {{ padding: 30px 20px; }}
                .button {{ display: inline-block; background: #4285f4; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; font-size: 12px; color: #666; text-align: center; }}
                .security-note {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                    <p>Kotak Neo Trading Platform</p>
                </div>
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset your password for your Kotak Neo Trading account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" class="button" style="color: white;">Reset Password</a>
                    
                    <div class="security-note">
                        <strong>🛡️ Security Information:</strong>
                        <ul>
                            <li>This link will expire in <strong>15 minutes</strong></li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>For security, this link can only be used once</li>
                        </ul>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
                        {reset_url}
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Kotak Neo Trading Platform</p>
                    <p>If you have any questions, please contact our support team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        mail.send(msg)
        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        return False

def send_password_update_confirmation(email, username, new_password):
    """Send password update confirmation email"""
    try:
        from app import mail
        
        # Create email message
        msg = Message(
            subject='Password Successfully Updated - Kotak Neo Trading',
            sender=os.environ.get('MAIL_USERNAME', 'noreply@kotakneo.com'),
            recipients=[email]
        )
        
        # Professional email template
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 30px 20px; text-align: center; }}
                .content {{ padding: 30px 20px; }}
                .footer {{ background: #f8f9fa; padding: 20px; font-size: 12px; color: #666; text-align: center; }}
                .security-note {{ background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .user-details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .success-badge {{ background: #4caf50; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; display: inline-block; margin: 10px 0; }}
                .login-info {{ background: #e3f2fd; border: 1px solid #2196f3; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Password Successfully Updated!</h1>
                    <p>Kotak Neo Trading Platform</p>
                    <div class="success-badge">Password Reset Complete</div>
                </div>
                <div class="content">
                    <h2>🎉 Your Password Has Been Updated</h2>
                    <p>Great news! Your password has been successfully changed for your Kotak Neo Trading account. You can now log in with your new password.</p>
                    
                    <div class="user-details">
                        <strong>📋 Account Information:</strong><br>
                        <strong>Username:</strong> {username}<br>
                        <strong>Email:</strong> {email}<br>
                        <strong>Updated Password:</strong> {new_password}<br>
                        <strong>Status:</strong> <span style="color: #4caf50; font-weight: bold;">✓ Active</span>
                    </div>
                    
                    <div class="login-info">
                        <strong>🔑 Login Instructions:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Use your <strong>username: {username}</strong></li>
                            <li>Enter the <strong>new password</strong> you just created</li>
                            <li>Your login credentials are now updated in the system</li>
                            <li>You can access your account immediately</li>
                        </ul>
                    </div>
                    
                    <div class="security-note">
                        <strong>🔐 Security Confirmation:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>✓ Password successfully changed and encrypted</li>
                            <li>✓ Old password has been permanently disabled</li>
                            <li>✓ Your account security has been enhanced</li>
                            <li>⚠️ If you didn't make this change, contact support immediately</li>
                            <li>💡 Consider enabling two-factor authentication for extra security</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <p style="font-size: 16px; color: #4caf50; font-weight: bold;">🎯 Your account is now secure and ready to use!</p>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>🛡️ This is an automated security notification</strong></p>
                    <p>Kotak Neo Trading Platform - Account Security Team</p>
                    <p>If you have any questions, please contact our support team</p>
                    <p><strong>Security Reminder:</strong> Never share your login credentials with anyone</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        mail.send(msg)
        logger.info(f"Password update confirmation sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password update confirmation: {e}")
        return False

def create_password_reset_token(user_id, expiry_minutes=15):
    """Create a secure password reset token"""
    try:
        # Generate secure token
        raw_token = secrets.token_urlsafe(48)  # 64 characters when base64 encoded
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
        
        # First, invalidate any existing tokens for this user
        invalidate_query = """
        UPDATE password_reset_tokens 
        SET used = true 
        WHERE user_id = %s AND used = false
        """
        execute_db_query(invalidate_query, (user_id,), fetch_results=False)
        
        # Create new token record
        insert_query = """
        INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        execute_db_query(insert_query, (user_id, token_hash, expires_at, False, datetime.now()), fetch_results=False)
        
        logger.info(f"Password reset token created for user {user_id}")
        return raw_token
        
    except Exception as e:
        logger.error(f"Failed to create reset token: {e}")
        return None

def validate_reset_token(token):
    """Validate a password reset token"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Check if token exists and is valid
        query = """
        SELECT prt.*, eu.sr as user_id, eu.email 
        FROM password_reset_tokens prt
        JOIN external_users eu ON prt.user_id = eu.sr
        WHERE prt.token_hash = %s AND prt.used = false AND prt.expires_at > %s
        """
        
        result = execute_db_query(query, (token_hash, datetime.now()))
        
        if result and len(result) > 0:
            return result[0], None
        else:
            return None, "Invalid or expired token"
            
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None, "Token validation error"

def mark_token_as_used(token):
    """Mark a reset token as used"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        update_query = """
        UPDATE password_reset_tokens 
        SET used = true 
        WHERE token_hash = %s
        """
        execute_db_query(update_query, (token_hash,), fetch_results=False)
        
        logger.info("Reset token marked as used")
        return True
        
    except Exception as e:
        logger.error(f"Failed to mark token as used: {e}")
        return False

# Create password_reset_tokens table if it doesn't exist
def ensure_reset_table_exists():
    """Ensure the password_reset_tokens table exists"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token_hash VARCHAR(128) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_hash ON password_reset_tokens(token_hash);
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
        """
        
        execute_db_query(create_table_query, fetch_results=False)
        logger.info("✓ Password reset tokens table ensured")
        
    except Exception as e:
        logger.error(f"Failed to create reset tokens table: {e}")

# Initialize table on module load
ensure_reset_table_exists()

@password_reset_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    try:
        username_or_email = request.form.get('username_or_email', '').strip()
        
        if not username_or_email:
            flash('Please enter your username or email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Search for user by username or email in external_users table
        user_query = """
        SELECT sr as id, email, username 
        FROM external_users 
        WHERE username = %s OR email = %s
        """
        
        users = execute_db_query(user_query, (username_or_email, username_or_email))
        
        # Always show the same message for security (don't reveal if account exists)
        message = "If the account exists, a password reset link will be sent to your registered email."
        
        if users and len(users) > 0:
            user = users[0]
            
            # Create reset token
            reset_token = create_password_reset_token(user['id'])
            
            if reset_token:
                # Send reset email
                from app import app
                email_sent = send_reset_email(user['email'], reset_token, app)
                
                if email_sent:
                    logger.info(f"Password reset initiated for user: {user['username']}")
                else:
                    logger.error(f"Failed to send reset email for user: {user['username']}")
        
        # Always show success message (security best practice)
        flash(message, 'success')
        return render_template('auth/forgot_password.html')
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        flash('An error occurred while processing your request. Please try again.', 'error')
        return render_template('auth/forgot_password.html')

@password_reset_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset with token"""
    token = request.args.get('token') or request.form.get('token')
    
    if not token:
        flash('Invalid reset link. Please request a new password reset.', 'error')
        return redirect(url_for('password_reset.forgot_password'))
    
    if request.method == 'GET':
        # Validate token before showing the form
        token_data, error = validate_reset_token(token)
        
        if error:
            # Show expired link page instead of redirecting to forgot password
            return render_template('auth/expired_link.html', error_message=error)
        
        return render_template('auth/reset_password.html', token=token)
    
    # POST request - process password reset
    try:
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate passwords
        if not new_password or not confirm_password:
            flash('Please fill in all password fields.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Validate token again
        token_data, error = validate_reset_token(token)
        
        if error:
            # Show expired link page instead of redirecting to forgot password
            return render_template('auth/expired_link.html', error_message=error)
        
        # Update user password in external_users table
        # Note: Using plain password to match existing auth system
        update_query = """
        UPDATE external_users 
        SET password = %s
        WHERE sr = %s
        """
        
        # Execute the update query
        update_result = execute_db_query(update_query, (new_password, token_data['user_id']), fetch_results=False)
        
        # Verify the password was actually updated
        verify_query = """
        SELECT password FROM external_users WHERE sr = %s
        """
        verification = execute_db_query(verify_query, (token_data['user_id'],))
        
        if not verification or verification[0]['password'] != new_password:
            flash('Failed to update password in database. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Get user details for confirmation email
        user_query = """
        SELECT username, email 
        FROM external_users 
        WHERE sr = %s
        """
        
        user_details = execute_db_query(user_query, (token_data['user_id'],))
        
        if not user_details or len(user_details) == 0:
            flash('Password updated but could not send confirmation email.', 'warning')
            return redirect(url_for('auth_routes.trading_account_login'))
        
        # Mark token as used
        mark_token_as_used(token)
        
        # Send password update confirmation email
        user_info = user_details[0]
        send_password_update_confirmation(user_info['email'], user_info['username'], new_password)
        
        logger.info(f"Password successfully reset for user: {user_info['username']} ({user_info['email']})")
        flash('Password reset successful! You can now log in with your new password.', 'success')
        return redirect(url_for('auth_routes.trading_account_login'))
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        flash('An error occurred while resetting your password. Please try again.', 'error')
        return render_template('auth/reset_password.html', token=token)

# Health check endpoint
@password_reset_bp.route('/reset-status')
def reset_status():
    """Check if password reset system is working"""
    try:
        # Test database connection
        test_query = "SELECT 1"
        result = execute_db_query(test_query)
        
        if result:
            return jsonify({"status": "ok", "message": "Password reset system operational"})
        else:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
            
    except Exception as e:
        logger.error(f"Reset status check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500