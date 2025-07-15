"""
Real-time Quotes API endpoints - DISABLED
This functionality has been removed.
"""

from flask import Blueprint, jsonify
import logging

quotes_bp = Blueprint('quotes', __name__, url_prefix='/api/quotes')
logger = logging.getLogger(__name__)

@quotes_bp.route('/latest', methods=['GET'])
def get_latest_quotes():
    """Get latest quotes - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Real-time quotes functionality has been disabled'
    }), 404

@quotes_bp.route('/symbols', methods=['GET'])
def get_tracked_symbols():
    """Get tracked symbols - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Symbol tracking functionality has been disabled'
    }), 404

@quotes_bp.route('/history/<symbol>', methods=['GET'])
def get_quote_history(symbol):
    """Get quote history - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Quote history functionality has been disabled'
    }), 404

@quotes_bp.route('/force-update', methods=['POST'])
def force_quote_update():
    """Force quote update - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Quote update functionality has been disabled'
    }), 404

@quotes_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Get scheduler status - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Scheduler functionality has been disabled'
    }), 404

@quotes_bp.route('/statistics', methods=['GET'])
def get_quote_statistics():
    """Get quote statistics - functionality disabled"""
    return jsonify({
        'success': False,
        'message': 'Quote statistics functionality has been disabled'
    }), 404