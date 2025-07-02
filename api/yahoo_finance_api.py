
from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from Scripts.yahoo_finance_service import yahoo_service
from Scripts.yahoo_scheduler import force_yahoo_update

yahoo_bp = Blueprint('yahoo', __name__, url_prefix='/api/yahoo')
logger = logging.getLogger(__name__)

@yahoo_bp.route('/update-prices', methods=['POST'])
def update_prices():
    """Force update prices from Yahoo Finance"""
    try:
        logger.info("Manual price update requested via API")
        
        # Update admin signals
        signals_updated = yahoo_service.update_admin_signals_prices()
        
        # Update realtime quotes
        quotes_updated = yahoo_service.update_realtime_quotes()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {signals_updated} signals and {quotes_updated} quotes',
            'signals_updated': signals_updated,
            'quotes_updated': quotes_updated,
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'Yahoo Finance'
        })
        
    except Exception as e:
        logger.error(f"Error in manual price update: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update prices from Yahoo Finance'
        }), 500

@yahoo_bp.route('/price/<symbol>', methods=['GET'])
def get_symbol_price(symbol):
    """Get current price for a specific symbol"""
    try:
        price_data = yahoo_service.get_stock_price(symbol)
        
        if price_data:
            return jsonify({
                'success': True,
                'data': price_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f'No price data found for {symbol}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@yahoo_bp.route('/prices', methods=['POST'])
def get_multiple_prices():
    """Get prices for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        prices = yahoo_service.get_multiple_prices(symbols)
        
        return jsonify({
            'success': True,
            'data': prices,
            'count': len(prices)
        })
        
    except Exception as e:
        logger.error(f"Error fetching multiple prices: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@yahoo_bp.route('/status', methods=['GET'])
def get_status():
    """Get Yahoo Finance service status"""
    try:
        # Get last update times from database
        from Scripts.models_etf import AdminTradeSignal
        
        latest_signal = AdminTradeSignal.query.filter(
            AdminTradeSignal.last_update_time.isnot(None)
        ).order_by(AdminTradeSignal.last_update_time.desc()).first()
        
        last_update = latest_signal.last_update_time if latest_signal else None
        
        return jsonify({
            'success': True,
            'service': 'Yahoo Finance',
            'status': 'active',
            'last_update': last_update.isoformat() if last_update else None,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting Yahoo Finance status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
