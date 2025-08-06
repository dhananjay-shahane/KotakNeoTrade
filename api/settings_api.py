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
    Save email notification settings for the current user in external_users table only
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

        # Get email notification setting
        email_notification = bool(data.get('email_notification', False))

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
            
            # Update email notification setting in external_users table
            cursor.execute("""
                UPDATE external_users 
                SET email_notification = %s 
                WHERE username = %s
            """, (email_notification, username))
            
            if cursor.rowcount == 0:
                logger.warning(f"No rows updated for username: {username}")
                return jsonify({
                    'success': False,
                    'error': 'User not found in external_users table'
                }), 404
            
            conn.commit()
            logger.info(f"✅ Email notification setting updated for {username}: {email_notification}")
            
            return jsonify({
                'success': True,
                'message': 'Email notification setting saved successfully'
            })

    except Exception as e:
        logger.error(f"❌ Failed to save email notification setting: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save email notification setting'
        }), 500
    finally:
        if conn:
            conn.close()


def get_users_with_email_notifications():
    """
    Get all users who have enabled email notifications from external_users table
    Used for sending emails when deals are created
    
    Returns:
        List of users with their email addresses who want notifications
    """
    conn = None
    try:
        conn = get_db_dict_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return []

        with conn.cursor() as cursor:
            # Get users who want deal notifications from external_users table
            cursor.execute("""
                SELECT username, email
                FROM external_users 
                WHERE email_notification = TRUE 
                AND email IS NOT NULL 
                AND email != ''
            """)

            results = cursor.fetchall()
            return [{'username': row[0], 'email': row[1]} for row in results] if results else []

    except Exception as e:
        logger.error(f"Error getting users with email notifications: {e}")
        return []
    finally:
        if conn:
            conn.close()