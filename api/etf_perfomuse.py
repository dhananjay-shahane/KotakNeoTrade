
from flask import Blueprint, request, jsonify, session
import logging
from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
from Scripts.external_db_service import get_etf_signals_data_json
import time

etf_performance_bp = Blueprint('etf_performance', __name__, url_prefix='/api/etf-performance')
logger = logging.getLogger(__name__)

@etf_performance_bp.route('/update-live-data', methods=['POST'])
def update_live_performance_data():
    """Update live performance data from Google Finance"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        logger.info("🚀 Starting live performance data update from Google Finance")
        
        start_time = time.time()
        updater = GoogleFinanceCMPUpdater()
        
        # Get all symbols and update them with historical data
        symbols = updater.get_symbols_from_database()
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols found in database'
            }), 400
        
        updated_count = 0
        performance_updates = {}
        
        # Update performance data for each symbol
        for symbol in symbols[:15]:  # Limit to 15 symbols for faster response
            try:
                logger.info(f"📊 Updating performance for {symbol}")
                
                # Fetch comprehensive historical data
                historical_data = updater.fetch_historical_data(symbol)
                
                if historical_data:
                    # Update database with performance metrics
                    rows_updated = updater.update_symbol_with_historical_data(symbol, historical_data)
                    
                    if rows_updated > 0:
                        updated_count += rows_updated
                        performance_updates[symbol] = {
                            'cmp': historical_data.get('cmp'),
                            'd30': historical_data.get('d30'),
                            'ch30': f"{historical_data.get('ch30', 0):.2f}%",
                            'd7': historical_data.get('d7'),
                            'ch7': f"{historical_data.get('ch7', 0):.2f}%"
                        }
                        
                        logger.info(f"✅ {symbol}: 30d={historical_data.get('ch30', 0):.2f}%, 7d={historical_data.get('ch7', 0):.2f}%")
                    
            except Exception as e:
                logger.error(f"❌ Error updating {symbol}: {e}")
                continue
        
        duration = time.time() - start_time
        
        # Get fresh datatable data
        fresh_data = get_etf_signals_data_json()
        
        logger.info(f"✅ Performance update completed in {duration:.2f}s, updated {updated_count} records")
        
        return jsonify({
            'success': True,
            'message': f'Updated performance data for {len(performance_updates)} symbols',
            'updated_count': updated_count,
            'duration': duration,
            'performance_updates': performance_updates,
            'data': fresh_data['data'],
            'recordsTotal': fresh_data['recordsTotal']
        })
        
    except Exception as e:
        logger.error(f"❌ Live performance update error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update live performance data'
        }), 500

@etf_performance_bp.route('/get-symbol-performance/<symbol>', methods=['GET'])
def get_symbol_performance(symbol):
    """Get performance data for a specific symbol"""
    try:
        updater = GoogleFinanceCMPUpdater()
        historical_data = updater.fetch_historical_data(symbol)
        
        if historical_data:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'performance': {
                    'current_price': historical_data.get('cmp'),
                    '30_day_price': historical_data.get('d30'),
                    '30_day_change': f"{historical_data.get('ch30', 0):.2f}%",
                    '7_day_price': historical_data.get('d7'),
                    '7_day_change': f"{historical_data.get('ch7', 0):.2f}%"
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Could not fetch performance data for {symbol}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting performance for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
