
from flask import Blueprint, request, jsonify, session
import psycopg2
import logging
import os

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/api')

def get_external_db_connection():
    """Get connection to external PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('EXTERNAL_DB_HOST', 'localhost'),
            database=os.getenv('EXTERNAL_DB_NAME', 'postgres'),
            user=os.getenv('EXTERNAL_DB_USER', 'postgres'),
            password=os.getenv('EXTERNAL_DB_PASSWORD', ''),
            port=os.getenv('EXTERNAL_DB_PORT', 5432)
        )
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to external database: {e}")
        return None

@password_reset_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset user password in external database with enhanced validation"""
    try:
        logging.info("Password reset request received")
        
        # Check if user is authenticated
        if not session.get('authenticated'):
            logging.warning("Unauthenticated password reset attempt")
            return jsonify({
                'success': False,
                'message': 'User not authenticated'
            }), 401
        
        data = request.get_json()
        if not data:
            logging.warning("No data provided in password reset request")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        old_password = data.get('oldPassword', '').strip()
        new_password = data.get('newPassword', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        username = session.get('username')
        
        logging.info(f"Password reset attempt for user: {username}")
        
        # Validation
        if not old_password or not new_password or not confirm_password:
            return jsonify({
                'success': False,
                'message': 'All password fields are required'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'New password and confirm password do not match'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username not found in session'
            }), 400
        
        # Connect to external database
        conn = get_external_db_connection()
        if not conn:
            logging.error("Failed to connect to external database")
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # First, verify the old password
            cursor.execute('''
                SELECT password FROM public.external_users 
                WHERE username = %s
            ''', (username,))
            
            current_user = cursor.fetchone()
            if not current_user:
                cursor.close()
                conn.close()
                logging.warning(f"User not found in database: {username}")
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            current_password = current_user[0]
            
            # Verify old password matches (case-sensitive comparison)
            if old_password != current_password:
                cursor.close()
                conn.close()
                logging.warning(f"Incorrect current password for user: {username}")
                return jsonify({
                    'success': False,
                    'message': 'Current password is incorrect'
                }), 400
            
            # Check if new password is same as current password
            if new_password == current_password:
                cursor.close()
                conn.close()
                logging.warning(f"User attempted to set same password: {username}")
                return jsonify({
                    'success': False,
                    'message': 'New password cannot be the same as your current password. Please choose a different password.'
                }), 400
            
            # Update password in external_users table
            cursor.execute('''
                UPDATE public.external_users 
                SET password = %s 
                WHERE username = %s
            ''', (new_password, username))
            
            # Check if update was successful
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                logging.error(f"Password update failed - no rows affected for user: {username}")
                return jsonify({
                    'success': False,
                    'message': 'Password not updated'
                }), 400
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logging.info(f"Password updated successfully for user: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Password updated successfully'
            })
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
                cursor.close()
                conn.close()
            logging.error(f"PostgreSQL error during password update: {e}")
            return jsonify({
                'success': False,
                'message': 'Database error occurred'
            }), 500
        except Exception as e:
            if conn:
                conn.rollback()
                cursor.close()
                conn.close()
            logging.error(f"Unexpected error during password update: {e}")
            return jsonify({
                'success': False,
                'message': 'Database error occurred'
            }), 500
        
    except Exception as e:
        logging.error(f"Error in reset_password: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
