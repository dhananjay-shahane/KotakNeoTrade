"""
Email Notification Status API
Dedicated endpoint to check and update email notification status
"""

import logging
from flask import Blueprint, session, request, jsonify
from config.database_config import get_db_dict_connection

logger = logging.getLogger(__name__)

# Create blueprint for email notification status
email_status_bp = Blueprint('email_status', __name__, url_prefix='/api')


@email_status_bp.route('/check-email-notification-status', methods=['GET'])
def check_email_notification_status():
    """
    Check current email notification status for authenticated user
    Returns the current state from external_users table
    """
    conn = None
    try:
        logger.info("📧 Email notification status check initiated")
        
        # Check authentication
        if not session.get('authenticated'):
            logger.warning("🔒 User not authenticated for email settings")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'User not authenticated'
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
            # Check if email_notification column exists, add if not
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'external_users' 
                AND column_name = 'email_notification'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE external_users ADD COLUMN email_notification BOOLEAN DEFAULT FALSE")
                conn.commit()
                logger.info("✅ Added email_notification column to external_users table")

            # Get current status
            cursor.execute("""
                SELECT email_notification, email, username
                FROM external_users 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            logger.info(f"Database query result for {username}: {result}")
            
            if result:
                email_notification = result.get('email_notification') if isinstance(result, dict) else (result[0] if result[0] is not None else False)
                user_email = result.get('email') if isinstance(result, dict) else (result[1] if len(result) > 1 and result[1] else session.get('email', ''))
                
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'status': {
                        'email_notification': bool(email_notification),
                        'user_email': user_email,
                        'username': username
                    }
                })
            else:
                # User not found, create entry with default values
                try:
                    cursor.execute("""
                        INSERT INTO external_users (username, email_notification, email) 
                        VALUES (%s, FALSE, %s)
                        ON CONFLICT (username) DO NOTHING
                    """, (username, session.get('email', '')))
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'authenticated': True,
                        'status': {
                            'email_notification': False,
                            'user_email': session.get('email', ''),
                            'username': username
                        }
                    })
                except Exception as insert_error:
                    logger.error(f"❌ Error creating user entry: {insert_error}")
                    return jsonify({
                        'success': False,
                        'error': 'User not found in external_users table'
                    }), 404

    except Exception as e:
        logger.error(f"❌ Error checking email notification status: {e}")
        logger.error(f"❌ Exception type: {type(e)}")
        logger.error(f"❌ Exception args: {e.args}")
        
        # Return proper JSON response even for errors
        try:
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': f'Database error: {str(e)}'
            }), 500
        except Exception as json_error:
            logger.error(f"❌ Failed to create JSON response: {json_error}")
            # Return plain text as last resort
            return f"Error: {str(e)}", 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


@email_status_bp.route('/update-email-notification-status', methods=['POST'])
def update_email_notification_status():
    """
    Update email notification status for authenticated user
    Accepts true/false values and saves to database
    """
    conn = None
    try:
        # Check authentication
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'User not authenticated'
            }), 401

        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username not found in session'
            }), 400

        data = request.get_json()
        if not data or 'email_notification' not in data:
            return jsonify({
                'success': False,
                'error': 'email_notification value required'
            }), 400

        # Convert to boolean explicitly
        email_notification = bool(data.get('email_notification'))

        conn = get_db_dict_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500

        with conn.cursor() as cursor:
            # Ensure column exists
            cursor.execute("ALTER TABLE external_users ADD COLUMN IF NOT EXISTS email_notification BOOLEAN DEFAULT FALSE")
            conn.commit()
            
            # Update the status
            cursor.execute("""
                UPDATE external_users 
                SET email_notification = %s 
                WHERE username = %s
            """, (email_notification, username))
            
            if cursor.rowcount == 0:
                return jsonify({
                    'success': False,
                    'error': 'User not found in external_users table'
                }), 404
            
            conn.commit()
            logger.info(f"✅ Updated email notification status for {username}: {email_notification}")
            
            # Return the updated status
            return jsonify({
                'success': True,
                'message': 'Email notification status updated successfully',
                'status': {
                    'email_notification': email_notification,
                    'username': username
                }
            })

    except Exception as e:
        logger.error(f"❌ Error updating email notification status: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update email notification status'
        }), 500
    finally:
        if conn:
            conn.close()