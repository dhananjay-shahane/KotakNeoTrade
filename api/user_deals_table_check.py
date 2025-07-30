
"""
API to check if user deals table exists
"""
from flask import Blueprint, jsonify, session
import logging
from scripts.dynamic_user_deals import dynamic_deals_service

user_deals_table_check_bp = Blueprint('user_deals_table_check', __name__, url_prefix='/api')

@user_deals_table_check_bp.route('/check-user-deals-table', methods=['GET'])
def check_user_deals_table():
    """Check if user deals table exists"""
    try:
        # Get username from session
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'message': 'User not authenticated',
                'table_exists': False
            }), 401

        # Check if table exists
        table_exists = dynamic_deals_service.table_exists(username)
        
        # If table exists, check if it has any data
        has_data = False
        if table_exists:
            deals = dynamic_deals_service.get_user_deals(username)
            has_data = len(deals) > 0

        return jsonify({
            'success': True,
            'table_exists': table_exists,
            'has_data': has_data,
            'table_name': f'{username}_deals',
            'username': username
        })

    except Exception as e:
        logging.error(f"Error checking user deals table: {e}")
        return jsonify({
            'success': False,
            'message': f'Error checking table: {str(e)}',
            'table_exists': False
        }), 500
