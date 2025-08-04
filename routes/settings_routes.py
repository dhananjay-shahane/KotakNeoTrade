"""
Settings routes for user preferences and configuration
"""
from flask import Blueprint, render_template, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

settings_routes = Blueprint('settings_routes', __name__, url_prefix='/settings')

@settings_routes.route('/')
def settings_page():
    """Settings page"""
    user_email = session.get('user_email', 'Not configured')
    return render_template('settings.html', user_email=user_email)

@settings_routes.route('/api/save-settings', methods=['POST'])
def save_settings_route():
    """Route wrapper for save_settings"""
    return save_settings()

@settings_routes.route('/save-settings', methods=['POST'])  # Alternative route
def save_settings():
    """Save user settings to session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Save settings to session
        session['email_settings'] = {
            'emailDealCreated': data.get('emailDealCreated', True),
            'emailDealUpdated': data.get('emailDealUpdated', True), 
            'emailDealClosed': data.get('emailDealClosed', True)
        }
        
        session['general_settings'] = {
            'autoRefresh': data.get('autoRefresh', True),
            'showINR': data.get('showINR', True)
        }
        
        logger.info(f"Settings saved for user: {session.get('username', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500