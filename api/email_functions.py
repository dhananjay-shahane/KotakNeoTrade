"""
Email Functions API for Kotak Neo Trading Platform
Integration functions for the 4 email notification cases
"""
import logging
from flask import Blueprint, request, jsonify, session
from functools import wraps
from typing import Dict, Any, Optional
from api.email_service import email_service

logger = logging.getLogger(__name__)

email_functions_bp = Blueprint('email_functions', __name__)

def login_required(f):
    """Decorator to require login for email functions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Integration Functions for Email Notifications

def trigger_trade_signal_email(signal_data: Dict[str, Any]) -> bool:
    """
    Trigger: When a new entry is added to the public.admin_trade_signals table
    Action: Send email to all external users with signal data
    """
    try:
        return email_service.send_trade_signal_notification(signal_data)
    except Exception as e:
        logger.error(f"Failed to trigger trade signal email: {e}")
        return False

def trigger_deal_creation_email(user_id: str, deal_data: Dict[str, Any]) -> bool:
    """
    Trigger: When logged-in user adds a new deal on Trading Signal page
    Action: Send email to logged-in user with deal details
    """
    try:
        return email_service.send_deal_creation_notification(user_id, deal_data)
    except Exception as e:
        logger.error(f"Failed to trigger deal creation email: {e}")
        return False

def setup_daily_subscription_email(user_id: str, send_time: str = "09:00") -> bool:
    """
    Setup daily trading signal change emails for subscribed users
    Activated when user turns on "Send daily change data" switch
    """
    try:
        email_service.setup_daily_trading_updates(user_id, send_time)
        return True
    except Exception as e:
        logger.error(f"Failed to setup daily subscription email: {e}")
        return False

def trigger_deal_status_email(user_id: str, deal_data: Dict[str, Any], action: str) -> bool:
    """
    Trigger: When user closes or deletes a deal on Deals page
    Action: Send email if user has email notifications enabled
    """
    try:
        return email_service.send_deal_status_notification(user_id, deal_data, action)
    except Exception as e:
        logger.error(f"Failed to trigger deal status email: {e}")
        return False

# API Endpoints for Email Management

@email_functions_bp.route('/api/email/test-connection', methods=['GET'])
@login_required
def test_email_connection():
    """Test email service configuration"""
    try:
        if email_service.is_configured:
            return jsonify({
                'status': 'success',
                'message': 'Email service is properly configured',
                'configured': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Email service not configured - check environment variables',
                'configured': False
            }), 500
    except Exception as e:
        logger.error(f"Email connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'configured': False
        }), 500

@email_functions_bp.route('/api/email/send-test', methods=['POST'])
@login_required
def send_test_email():
    """Send a test email to verify functionality"""
    try:
        data = request.get_json()
        test_email = data.get('email')
        
        if not test_email:
            return jsonify({'error': 'Email address required'}), 400
            
        subject = "Test Email from Trading Platform"
        text_content = """
This is a test email from your Kotak Neo Trading Platform.

If you received this email, your email notifications are working correctly.

Best regards,
Trading Platform Team
        """.strip()
        
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Test Email Successful!</h2>
            <p>This is a test email from your Kotak Neo Trading Platform.</p>
            <p>If you received this email, your email notifications are working correctly.</p>
            <hr>
            <p><em>Best regards,<br>Trading Platform Team</em></p>
        </body>
        </html>
        """
        
        success = email_service.send_email(test_email, subject, text_content, html_content)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Test email sent successfully to {test_email}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test email'
            }), 500
            
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@email_functions_bp.route('/api/email/update-preference', methods=['POST'])
@login_required
def update_email_preference():
    """Update user's email notification preferences"""
    try:
        from config.database_config import execute_db_query
        
        data = request.get_json()
        user_id = session.get('user_id')
        alternative_email = data.get('alternative_email')
        
        # Update alternative email in users table
        if alternative_email:
            query = """
            UPDATE users 
            SET alternative_email = %s 
            WHERE username = %s
            """
            execute_db_query(query, (alternative_email, user_id))
            
        return jsonify({
            'status': 'success',
            'message': 'Email preference updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update email preference: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@email_functions_bp.route('/api/email/subscription', methods=['POST'])
@login_required
def update_subscription():
    """Update user's daily email subscription"""
    try:
        from config.database_config import execute_db_query
        
        data = request.get_json()
        user_id = session.get('user_id')
        subscription = data.get('subscription', False)
        send_time = data.get('send_time', '09:00')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401
        
        # Update subscription in users table
        query = """
        UPDATE users 
        SET subscription = %s 
        WHERE username = %s
        """
        execute_db_query(query, (subscription, user_id))
        
        # Setup daily emails if subscription is enabled
        if subscription:
            setup_daily_subscription_email(str(user_id), send_time)
            
        return jsonify({
            'status': 'success',
            'message': f'Subscription {"enabled" if subscription else "disabled"} successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update subscription: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@email_functions_bp.route('/api/email/notification-settings', methods=['POST'])
@login_required
def update_notification_settings():
    """Update user's email notification settings"""
    try:
        from config.database_config import execute_db_query
        
        data = request.get_json()
        user_id = session.get('user_id')
        email_notification = data.get('email_notification', False)
        
        # Update email notification setting in external_users table
        query = """
        UPDATE external_users 
        SET email_notification = %s 
        WHERE username = %s
        """
        execute_db_query(query, (email_notification, user_id))
        
        return jsonify({
            'status': 'success',
            'message': f'Email notifications {"enabled" if email_notification else "disabled"} successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update notification settings: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Database Trigger Functions (to be called from other modules)

def on_admin_trade_signal_insert(signal_data: Dict[str, Any]):
    """
    Database trigger function - called when new signal is added to admin_trade_signals
    This should be integrated into the admin signals API
    """
    logger.info(f"New trade signal detected: {signal_data.get('symbol')}")
    trigger_trade_signal_email(signal_data)

def on_user_deal_insert(user_id: str, deal_data: Dict[str, Any]):
    """
    Database trigger function - called when user creates a new deal
    This should be integrated into the deals API
    """
    logger.info(f"New deal created by {user_id}: {deal_data.get('symbol')}")
    trigger_deal_creation_email(user_id, deal_data)

def on_user_deal_update(user_id: str, deal_data: Dict[str, Any], action: str):
    """
    Database trigger function - called when user closes/deletes a deal
    This should be integrated into the deals API
    """
    logger.info(f"Deal {action} by {user_id}: {deal_data.get('symbol')}")
    trigger_deal_status_email(user_id, deal_data, action)

# Helper function to prompt user for alternative email
def prompt_for_alternative_email(user_id: str) -> Optional[str]:
    """
    Helper function to get user's preferred email address
    Returns alternative email if set, otherwise regular email
    """
    return email_service.get_user_email_preference(user_id)