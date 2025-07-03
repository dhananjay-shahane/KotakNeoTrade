
from flask import Blueprint, request, jsonify
import logging
from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
from Scripts.external_db_service import get_etf_signals_from_external_db
import time

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')
logger = logging.getLogger(__name__)

@performance_bp.route('/update-all-performance', methods=['POST'])
def update_all_performance():
    """Update performance data (D30, CH30, D7, CH7) for all symbols"""
    try:
        logger.info("🚀 Starting comprehensive performance update with Google Finance data")
        
        start_time = time.time()
        updater = GoogleFinanceCMPUpdater()
        
        # Get all symbols from database
        symbols = updater.get_symbols_from_database()
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols found in database'
            }), 400
        
        updated_count = 0
        error_count = 0
        results = {}
        
        for symbol in symbols:
            try:
                logger.info(f"📊 Processing performance data for {symbol}")
                
                # Get historical data including performance metrics
                historical_data = updater.fetch_historical_data(symbol)
                
                if historical_data:
                    # Update database with comprehensive data
                    updated_rows = updater.update_symbol_with_historical_data(symbol, historical_data)
                    
                    if updated_rows > 0:
                        updated_count += updated_rows
                        results[symbol] = {
                            'success': True,
                            'data': historical_data,
                            'updated_rows': updated_rows
                        }
                        logger.info(f"✅ {symbol}: CMP=₹{historical_data.get('cmp', 0):.2f}, 30d={historical_data.get('ch30', 0):.2f}%, 7d={historical_data.get('ch7', 0):.2f}%")
                    else:
                        results[symbol] = {
                            'success': True,
                            'data': historical_data,
                            'updated_rows': 0,
                            'message': 'No database updates needed'
                        }
                else:
                    error_count += 1
                    results[symbol] = {
                        'success': False,
                        'error': 'Could not fetch historical data'
                    }
                    logger.warning(f"⚠️ Could not fetch performance data for {symbol}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"❌ Error processing {symbol}: {e}")
        
        duration = time.time() - start_time
        success_count = len([r for r in results.values() if r['success']])
        
        logger.info(f"✅ Performance update completed!")
        logger.info(f"   • Symbols processed: {len(symbols)}")
        logger.info(f"   • Successful updates: {success_count}")
        logger.info(f"   • Database rows updated: {updated_count}")
        logger.info(f"   • Errors: {error_count}")
        logger.info(f"   • Duration: {duration:.2f} seconds")
        
        return jsonify({
            'success': True,
            'message': f'Performance data updated for {success_count}/{len(symbols)} symbols',
            'symbols_processed': len(symbols),
            'successful_updates': success_count,
            'database_rows_updated': updated_count,
            'errors': error_count,
            'duration': duration,
            'results': results,
            'data_source': 'Google Finance Historical Data'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in performance update: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update performance data'
        }), 500

@performance_bp.route('/calculate-performance/<symbol>', methods=['GET'])
def calculate_performance_for_symbol(symbol):
    """Calculate performance metrics for a specific symbol"""
    try:
        updater = GoogleFinanceCMPUpdater()
        
        # Get historical data
        historical_data = updater.fetch_historical_data(symbol)
        
        if not historical_data:
            return jsonify({
                'success': False,
                'message': f'Could not fetch historical data for {symbol}'
            }), 404
        
        # Calculate additional metrics
        performance_metrics = {
            'symbol': symbol,
            'current_price': historical_data.get('cmp', 0),
            'thirty_day_price': historical_data.get('d30', 0),
            'thirty_day_change': historical_data.get('ch30', 0),
            'seven_day_price': historical_data.get('d7', 0),
            'seven_day_change': historical_data.get('ch7', 0),
            'net_price': historical_data.get('nt', 0)
        }
        
        return jsonify({
            'success': True,
            'data': performance_metrics,
            'message': f'Performance metrics calculated for {symbol}'
        })
        
    except Exception as e:
        logger.error(f"❌ Error calculating performance for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/update-specific-symbols', methods=['POST'])
def update_specific_symbols_performance():
    """Update performance data for specific symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'message': 'No symbols provided'
            }), 400
        
        logger.info(f"🎯 Updating performance data for specific symbols: {symbols}")
        
        start_time = time.time()
        updater = GoogleFinanceCMPUpdater()
        
        updated_count = 0
        error_count = 0
        results = {}
        
        for symbol in symbols:
            try:
                # Get historical data
                historical_data = updater.fetch_historical_data(symbol)
                
                if historical_data:
                    # Update database
                    updated_rows = updater.update_symbol_with_historical_data(symbol, historical_data)
                    updated_count += updated_rows
                    
                    results[symbol] = {
                        'success': True,
                        'data': historical_data,
                        'updated_rows': updated_rows
                    }
                else:
                    error_count += 1
                    results[symbol] = {
                        'success': False,
                        'error': 'Could not fetch historical data'
                    }
                
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
        
        duration = time.time() - start_time
        success_count = len([r for r in results.values() if r['success']])
        
        return jsonify({
            'success': True,
            'message': f'Performance data updated for {success_count}/{len(symbols)} symbols',
            'symbols_processed': len(symbols),
            'successful_updates': success_count,
            'database_rows_updated': updated_count,
            'errors': error_count,
            'duration': duration,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"❌ Error in specific symbols performance update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
