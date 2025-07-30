
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
        # Check if user is authenticated
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'message': 'User not authenticated'
            }), 401
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')
        username = session.get('username')
        
        # Validation
        if not new_password or not confirm_password:
            return jsonify({
                'success': False,
                'message': 'Both password fields are required'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
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
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        try:
            cursor = conn.cursor()
            
            # First, get the current password to check if it's the same
            cursor.execute('''
                SELECT password FROM public.external_users 
                WHERE username = %s
            ''', (username,))
            
            current_user = cursor.fetchone()
            if not current_user:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            current_password = current_user[0]
            
            # Check if new password is same as current password
            if new_password == current_password:
                cursor.close()
                conn.close()
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
            
        except Exception as e:
            if conn:
                conn.rollback()
                cursor.close()
                conn.close()
            logging.error(f"Database error during password update: {e}")
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
