
"""
Deals API endpoints for user deals management
"""
import logging
import sys
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

# Add scripts to path
sys.path.append('scripts')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

deals_api = Blueprint('deals_api', __name__, url_prefix='/api')


@deals_api.route('/deals', methods=['GET'])
@login_required
def get_deals():
    """Get user deals"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Import here to avoid circular imports
        from scripts.dynamic_user_deals import get_user_deals_data
        
        username = current_user.username
        deals = get_user_deals_data(username)
        
        return jsonify({
            'success': True,
            'data': deals,
            'deals': deals,  # For compatibility
            'total_count': len(deals)
        })
        
    except Exception as e:
        logger.error(f"Get deals API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/deals/<int:deal_id>/exit', methods=['POST', 'PUT'])
@login_required
def exit_deal(deal_id):
    """Exit a deal by updating its status"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json() or {}
        username = current_user.username
        
        # Import here to avoid circular imports
        from scripts.dynamic_user_deals import exit_user_deal
        
        result = exit_user_deal(username, deal_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Deal {deal_id} exited successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to exit deal'}), 500
            
    except Exception as e:
        logger.error(f"Exit deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/deals', methods=['POST'])
@login_required
def add_deal():
    """Add a new deal"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = current_user.username
        
        # Import here to avoid circular imports
        from scripts.dynamic_user_deals import add_user_deal
        
        deal_id = add_user_deal(username, data)
        
        if deal_id:
            return jsonify({
                'success': True,
                'message': 'Deal added successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add deal'}), 500
            
    except Exception as e:
        logger.error(f"Add deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/deals/<int:deal_id>', methods=['PUT'])
@login_required
def update_deal(deal_id):
    """Update an existing deal"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = current_user.username
        
        # Import here to avoid circular imports
        from scripts.dynamic_user_deals import update_user_deal
        
        result = update_user_deal(username, deal_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Deal {deal_id} updated successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update deal'}), 500
            
    except Exception as e:
        logger.error(f"Update deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/deals/<int:deal_id>', methods=['DELETE'])
@login_required
def delete_deal(deal_id):
    """Delete a deal"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        username = current_user.username
        
        # Import here to avoid circular imports
        from scripts.dynamic_user_deals import delete_user_deal
        
        result = delete_user_deal(username, deal_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Deal {deal_id} deleted successfully',
                'deal_id': deal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete deal'}), 500
            
    except Exception as e:
        logger.error(f"Delete deal API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
