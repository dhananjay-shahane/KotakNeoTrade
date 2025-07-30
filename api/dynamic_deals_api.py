"""
Dynamic User Deals API - External Database Integration
Handles user-specific deals operations with dynamic table creation
"""
import logging
import sys
from flask import Blueprint, request, jsonify, session
from flask_login import current_user, login_required

# Add scripts to path
sys.path.append('scripts')
from scripts.dynamic_user_deals import DynamicUserDealsService

# Initialize dynamic deals service
dynamic_deals_service = DynamicUserDealsService()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dynamic_deals_api = Blueprint('dynamic_deals_api', __name__, url_prefix='/api')


@dynamic_deals_api.route('/user-deals', methods=['GET'])
@login_required
def get_user_deals():
    """Get all deals from user-specific deals table"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        username = current_user.username
        
        # Get deals from user table
        deals = dynamic_deals_service.get_user_deals(username, current_user.id)
        
        return jsonify({
            'success': True,
            'data': deals,
            'total_count': len(deals),
            'table_name': f'{username}_deals'
        })
        
    except Exception as e:
        logger.error(f"Get user deals API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dynamic_deals_api.route('/user-deals/<int:deal_id>', methods=['PUT'])
@login_required  
def update_user_deal(deal_id):
    """Update a deal in user-specific deals table"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = current_user.username
        
        # Remove non-updatable fields
        updates = {k: v for k, v in data.items() if k not in ['id', 'created_at', 'user_id']}
        
        # Update deal
        success = dynamic_deals_service.update_deal(username, deal_id, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Deal {deal_id} updated successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update deal'}), 500
            
    except Exception as e:
        logger.error(f"Update user deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dynamic_deals_api.route('/user-deals/<int:deal_id>/close', methods=['POST'])
@login_required
def close_user_deal(deal_id):
    """Close a deal in user-specific deals table"""
    try:    
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        username = current_user.username
        
        # Close deal
        success = dynamic_deals_service.close_deal(username, deal_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Deal {deal_id} closed successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to close deal'}), 500
            
    except Exception as e:
        logger.error(f"Close user deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dynamic_deals_api.route('/user-deals', methods=['POST'])
@login_required
def add_user_deal():
    """Add a new deal to user-specific deals table"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = current_user.username
        
        # Check if user deals table exists, create if not
        if not dynamic_deals_service.table_exists(username):
            if not dynamic_deals_service.create_user_deals_table(username):
                return jsonify({'success': False, 'error': 'Failed to create user deals table'}), 500
        
        # Prepare deal data
        deal_data = {
            'user_id': current_user.id,
            'trade_signal_id': data.get('trade_signal_id'),
            'symbol': data.get('symbol'),
            'qty': data.get('qty'),
            'ep': data.get('ep'),
            'pos': data.get('pos'),
            'status': data.get('status', 'ACTIVE'),
            'target_price': data.get('target_price'),
            'stop_loss': data.get('stop_loss'),
            'notes': data.get('notes', '')
        }
        
        # Add deal to user table
        deal_id = dynamic_deals_service.add_deal_to_user_table(username, deal_data)
        
        if deal_id:
            return jsonify({
                'success': True,
                'message': f'Deal added successfully to {username}_deals table',
                'deal_id': deal_id,
                'table_name': f'{username}_deals'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add deal'}), 500
            
    except Exception as e:
        logger.error(f"Add user deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dynamic_deals_api.route('/user-table-status', methods=['GET'])
@login_required
def check_user_table_status():
    """Check if user deals table exists"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        username = current_user.username
        table_exists = dynamic_deals_service.table_exists(username)
        
        return jsonify({
            'success': True,
            'table_exists': table_exists,
            'table_name': f'{username}_deals',
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Check user table status API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500