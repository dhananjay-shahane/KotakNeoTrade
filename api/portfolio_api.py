"""
Portfolio API for fetching user deals statistics and data
"""
import logging
from flask import Blueprint, jsonify, session
from Scripts.user_deals_service import UserDealsService

logger = logging.getLogger(__name__)

# Create blueprint for portfolio API
portfolio_api = Blueprint('portfolio_api', __name__)

# Initialize user deals service
user_deals_service = UserDealsService()


@portfolio_api.route('/api/portfolio/stats')
def get_portfolio_stats():
    """Get portfolio statistics for dashboard cards and charts"""
    try:
        # Get user ID from session
        user_id = session.get('user_id', 1)
        
        logger.info(f"Fetching portfolio stats for user_id: {user_id}")
        
        # Fetch deals statistics
        deals_stats = user_deals_service.get_deals_statistics(user_id)
        
        logger.info(f"Portfolio stats result: {deals_stats}")
        
        return jsonify({
            'success': True,
            'data': deals_stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching portfolio stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'total_deals': 0,
                'active_deals': 0,
                'closed_deals': 0,
                'symbols': [],
                'symbol_chart_data': {'labels': [], 'data': [], 'colors': []},
                'status_chart_data': {'labels': [], 'data': [], 'colors': []},
                'deals_list': []
            }
        })


@portfolio_api.route('/api/portfolio/symbols')
def get_portfolio_symbols():
    """Get list of symbols from user deals"""
    try:
        user_id = session.get('user_id', 1)
        deals_stats = user_deals_service.get_deals_statistics(user_id)
        
        return jsonify({
            'success': True,
            'data': deals_stats.get('symbols', [])
        })
        
    except Exception as e:
        logger.error(f"Error fetching portfolio symbols: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        })


@portfolio_api.route('/api/portfolio/symbol-data/<symbol>')
def get_symbol_data(symbol):
    """Get detailed data for a specific symbol"""
    try:
        user_id = session.get('user_id', 1)
        
        # Get symbol-specific deals data
        symbol_data = user_deals_service.get_symbol_details(user_id, symbol)
        
        return jsonify({
            'success': True,
            'data': symbol_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching symbol data for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        })