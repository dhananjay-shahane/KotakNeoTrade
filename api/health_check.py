"""
Health Check API
Simple endpoint for connection testing
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health-check', methods=['GET', 'HEAD'])
def health_check():
    """Simple health check endpoint for connection testing"""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running'
    }), 200