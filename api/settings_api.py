"""
Email Settings API for Kotak Neo Trading Platform
Handles saving and retrieving user email notification preferences and SMTP configurations
"""

import json
import logging
from datetime import datetime
from flask import request, jsonify, session
from config.database_config import get_db_dict_connection
from security.input_validator import InputValidator

logger = logging.getLogger(__name__)


def create_user_settings_table():
    """
    Create user_email_settings table if it doesn't exist
    This table stores user-specific email notification preferences and SMTP configurations
    """
    try:
        conn = get_db_dict_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False

        with conn.cursor() as cursor:
            # Create table for storing user email settings with proper security measures
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_email_settings (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    user_email VARCHAR(255),
                    send_deals_in_mail BOOLEAN DEFAULT FALSE,
                    send_daily_change_data BOOLEAN DEFAULT FALSE,
                    subscription BOOLEAN DEFAULT FALSE,
                    daily_email_time VARCHAR(5) DEFAULT '11:00',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT valid_time_format CHECK (daily_email_time ~ '^[0-2][0-9]:[0-5][0-9]$')
                )
            """)
            
            # Create index for faster user lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_email_settings_username 
                ON user_email_settings(username)
            """)
            
            conn.commit()
            logger.info("✅ User email settings table created/verified successfully")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to create user settings table: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def get_user_email_settings():
    """
    Retrieve email notification settings for the current user
    Returns user's email preferences including switches and SMTP configuration
    """
    try:
        # Ensure user is authenticated before accessing settings
        if not session.get('authenticated'):
            return jsonify({
                'success': False, 
                'error': 'User authentication required'
            }), 401

        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username not found in session'
            }), 400

        conn = get_db_dict_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500

        with conn.cursor() as cursor:
            # Retrieve user settings with authorization check
            cursor.execute("""
                SELECT send_deals_in_mail, send_daily_change_data, daily_email_time, user_email
                FROM user_email_settings 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            
            # Get user's registered email from session as default
            user_session_email = session.get('email', '')
            
            if result:
                return jsonify({
                    'success': True,
                    'settings': {
                        'send_deals_in_mail': result[0] if result[0] is not None else False,
                        'send_daily_change_data': result[1] if result[1] is not None else False,
                        'daily_email_time': result[2] if result[2] is not None else '11:00',
                        'user_email': result[3] if result[3] else user_session_email
                    }
                })
            else:
                # Return default settings with user's session email pre-populated
                return jsonify({
                    'success': True,
                    'settings': {
                        'send_deals_in_mail': False,
                        'send_daily_change_data': False,
                        'daily_email_time': '11:00',
                        'user_email': user_session_email
                    }
                })

    except Exception as e:
        logger.error(f"❌ Failed to retrieve user email settings: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve email settings'
        }), 500
    finally:
        if conn:
            conn.close()


def save_user_email_settings():
    """
    Save email notification settings for the current user
    Validates input and performs authorization checks before saving preferences
    """
    try:
        # Ensure user is authenticated before saving settings
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'error': 'User authentication required'
            }), 401

        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username not found in session'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No settings data provided'
            }), 400

        # Validate input data with security checks
        send_deals_in_mail = bool(data.get('send_deals_in_mail', False))
        send_daily_change_data = bool(data.get('send_daily_change_data', False))
        daily_email_time = data.get('daily_email_time', '11:00')
        user_email = data.get('user_email', '').strip()
        
        # Link subscription status to daily change data checkbox
        subscription_status = send_daily_change_data

        # Validate time format (HH:MM)
        if not InputValidator.validate_time_format(daily_email_time):
            return jsonify({
                'success': False,
                'error': 'Invalid time format. Use HH:MM format'
            }), 400

        # Validate email format if user email is provided
        if user_email and not InputValidator.validate_email(user_email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400

        conn = get_db_dict_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500

        with conn.cursor() as cursor:
            # Use UPSERT to insert or update user settings
            cursor.execute("""
                INSERT INTO user_email_settings 
                (username, user_email, send_deals_in_mail, send_daily_change_data, subscription, daily_email_time, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (username) 
                DO UPDATE SET
                    user_email = EXCLUDED.user_email,
                    send_deals_in_mail = EXCLUDED.send_deals_in_mail,
                    send_daily_change_data = EXCLUDED.send_daily_change_data,
                    subscription = EXCLUDED.subscription,
                    daily_email_time = EXCLUDED.daily_email_time,
                    updated_at = CURRENT_TIMESTAMP
            """, (username, user_email, send_deals_in_mail, send_daily_change_data, subscription_status, daily_email_time))
            
            # Also update subscription status in external_users table
            try:
                cursor.execute("""
                    UPDATE external_users 
                    SET subscription = %s 
                    WHERE username = %s
                """, (subscription_status, username))
            except Exception as e:
                logger.warning(f"Could not update external_users subscription: {e}")
                # Try to add subscription column if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS subscription BOOLEAN DEFAULT FALSE")
                    cursor.execute("UPDATE external_users SET subscription = %s WHERE username = %s", (subscription_status, username))
                except Exception as e2:
                    logger.error(f"Failed to add subscription column or update: {e2}")
            
            conn.commit()
            logger.info(f"✅ Email settings saved successfully for user: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Email settings saved successfully'
            })

    except ValueError as e:
        logger.error(f"❌ Invalid input data: {e}")
        return jsonify({
            'success': False,
            'error': 'Invalid input data provided'
        }), 400
    except Exception as e:
        logger.error(f"❌ Failed to save user email settings: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save email settings'
        }), 500
    finally:
        if conn:
            conn.close()


def get_users_with_email_notifications(notification_type):
    """
    Get all users who have enabled specific email notification types
    Used for sending bulk emails when trading signals or deals are updated
    
    Args:
        notification_type: 'deals' or 'daily_reports'
    
    Returns:
        List of users with their email settings and SMTP configurations
    """
    try:
        conn = get_db_dict_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return []

        with conn.cursor() as cursor:
            if notification_type == 'deals':
                # Get users who want deal notifications
                cursor.execute("""
                    SELECT username, user_email
                    FROM user_email_settings 
                    WHERE send_deals_in_mail = TRUE 
                    AND user_email IS NOT NULL 
                    AND user_email != ''
                """)
            elif notification_type == 'daily_reports':
                # Get users who want daily reports (with subscription enabled)
                cursor.execute("""
                    SELECT username, user_email, daily_email_time
                    FROM user_email_settings 
                    WHERE send_daily_change_data = TRUE 
                    AND subscription = TRUE
                    AND user_email IS NOT NULL 
                    AND user_email != ''
                """)
            else:
                logger.error(f"Invalid notification type: {notification_type}")
                return []
            
            results = cursor.fetchall()
            logger.info(f"✅ Found {len(results)} users with {notification_type} notifications enabled")
            return results

    except Exception as e:
        logger.error(f"❌ Failed to get users with email notifications: {e}")
        return []
    finally:
        if conn:
            conn.close()


# Initialize the settings table when the module is imported
create_user_settings_table()