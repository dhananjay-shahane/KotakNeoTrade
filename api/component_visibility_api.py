"""
API endpoints for managing component visibility
"""

import logging
from flask import Blueprint, request, jsonify, session
from utils.component_visibility import component_manager

logger = logging.getLogger(__name__)

# Create blueprint for component visibility API
component_visibility_bp = Blueprint('component_visibility', __name__, url_prefix='/api/components')

@component_visibility_bp.route('/visibility', methods=['GET'])
def get_user_component_visibility():
    """Get component visibility settings for the current user"""
    try:
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        settings = component_manager.get_user_component_settings(username)
        
        return jsonify({
            'success': True,
            'data': settings,
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Error getting component visibility: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve component settings'
        }), 500

@component_visibility_bp.route('/visibility/<component_name>', methods=['GET'])
def check_component_visibility(component_name):
    """Check if a specific component is visible for the current user"""
    try:
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        is_visible = component_manager.is_component_visible(username, component_name)
        
        return jsonify({
            'success': True,
            'component': component_name,
            'visible': is_visible,
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Error checking component visibility: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check component visibility'
        }), 500

@component_visibility_bp.route('/visibility/<component_name>', methods=['POST'])
def update_component_visibility(component_name):
    """Update visibility status for a specific component (admin only)"""
    try:
        # Check authentication
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        # Get target username (defaults to current user)
        target_username = data.get('username', username)
        status = data.get('status')
        
        if not isinstance(status, bool):
            return jsonify({
                'success': False,
                'error': 'Status must be a boolean value'
            }), 400
        
        # Update component status
        success = component_manager.update_component_status(
            target_username, 
            component_name, 
            status
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Component {component_name} updated successfully',
                'component': component_name,
                'username': target_username,
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update component status'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating component visibility: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update component visibility'
        }), 500

@component_visibility_bp.route('/available', methods=['GET'])
def get_available_components():
    """Get list of all available components"""
    try:
        components = component_manager.get_available_components()
        
        return jsonify({
            'success': True,
            'components': components
        })
        
    except Exception as e:
        logger.error(f"Error getting available components: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve available components'
        }), 500

@component_visibility_bp.route('/initialize', methods=['POST'])
def initialize_user_components():
    """Initialize component settings for a user"""
    try:
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        data = request.get_json() or {}
        default_visible = data.get('default_visible', False)
        
        success = component_manager.initialize_user_settings(username, default_visible)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Component settings initialized for {username}',
                'username': username,
                'default_visible': default_visible
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to initialize component settings'
            }), 500
            
    except Exception as e:
        logger.error(f"Error initializing user components: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to initialize user components'
        }), 500