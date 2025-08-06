"""
Email Settings API

This module handles email notification settings for users using external_users table only.
It provides endpoints to get and save user email preferences.
"""

import logging
import re
from flask import session, request, jsonify
from config.database_config import get_db_dict_connection

logger = logging.getLogger(__name__)


def get_user_email_settings():
    """
    Retrieve email notification settings for the current user from external_users table
    Returns user's email preferences including notification switch
    """
    conn = None
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
            # Add email_notification column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS email_notification BOOLEAN DEFAULT FALSE")
                conn.commit()
            except Exception as e:
                logger.warning(f"Could not add email_notification column: {e}")
            
            # Retrieve user settings from external_users table
            cursor.execute("""
                SELECT email_notification, email, username
                FROM external_users 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            
            # Get user's registered email from session as default
            user_session_email = session.get('email', '')
            
            if result:
                return jsonify({
                    'success': True,
                    'settings': {
                        'email_notification': result[0] if result[0] is not None else False,
                        'user_email': result[1] if result[1] else user_session_email
                    }
                })
            else:
                # Return default settings with user's session email pre-populated
                return jsonify({
                    'success': True,
                    'settings': {
                        'email_notification': False,
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
    conn = None
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
        alternative_email = data.get('alternative_email', '').strip()
        
        # Link subscription status to daily change data checkbox
        subscription_status = send_daily_change_data

        # Validate time format (HH:MM)
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', daily_email_time):
            return jsonify({
                'success': False,
                'error': 'Invalid time format. Use HH:MM format'
            }), 400

        # Validate email format if user email is provided
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if user_email and not re.match(email_pattern, user_email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
            
        # Validate alternative email format if provided
        if alternative_email and not re.match(email_pattern, alternative_email):
            return jsonify({
                'success': False,
                'error': 'Invalid alternative email format'
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
                (username, user_email, alternative_email, send_deals_in_mail, send_daily_change_data, subscription, daily_email_time, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (username) 
                DO UPDATE SET
                    user_email = EXCLUDED.user_email,
                    alternative_email = EXCLUDED.alternative_email,
                    send_deals_in_mail = EXCLUDED.send_deals_in_mail,
                    send_daily_change_data = EXCLUDED.send_daily_change_data,
                    subscription = EXCLUDED.subscription,
                    daily_email_time = EXCLUDED.daily_email_time,
                    updated_at = CURRENT_TIMESTAMP
            """, (username, user_email, alternative_email, send_deals_in_mail, send_daily_change_data, subscription_status, daily_email_time))
            
            # Also update subscription status and email notification in external_users table
            try:
                # Add email_notification column if it doesn't exist
                cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS email_notification BOOLEAN DEFAULT FALSE")
                cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS subscription BOOLEAN DEFAULT FALSE")
                
                # Also ensure user_email_settings table has alternative_email column
                cursor.execute("ALTER TABLE user_email_settings ADD COLUMN IF NOT EXISTS alternative_email VARCHAR(255)")
                
                # Update both subscription and email notification based on send_deals_in_mail setting
                cursor.execute("""
                    UPDATE external_users 
                    SET subscription = %s, email_notification = %s 
                    WHERE username = %s
                """, (subscription_status, send_deals_in_mail, username))
                
                logger.info(f"✅ Updated external_users table for {username}: subscription={subscription_status}, email_notification={send_deals_in_mail}")
                
            except Exception as e:
                logger.warning(f"Could not update external_users: {e}")
                # Try to add columns separately if needed
                try:
                    cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS subscription BOOLEAN DEFAULT FALSE")
                    cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS email_notification BOOLEAN DEFAULT FALSE")
                    cursor.execute("ALTER TABLE user_email_settings ADD COLUMN IF NOT EXISTS alternative_email VARCHAR(255)")
                    cursor.execute("UPDATE external_users SET subscription = %s, email_notification = %s WHERE username = %s", 
                                 (subscription_status, send_deals_in_mail, username))
                except Exception as e2:
                    logger.error(f"Failed to add columns or update external_users: {e2}")
            
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
    conn = None
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
                return []

            results = cursor.fetchall()
            return [dict(row) for row in results] if results else []

    except Exception as e:
        logger.error(f"Error getting users with email notifications: {e}")
        return []
    finally:
        if conn:
            conn.close()