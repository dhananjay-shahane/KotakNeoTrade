
from flask import Blueprint, request, jsonify
import logging
import time
from datetime import datetime
from Scripts.yahoo_finance_service import yahoo_service
from Scripts.yahoo_scheduler import force_yahoo_update

yahoo_bp = Blueprint('yahoo', __name__, url_prefix='/api/yahoo')
logger = logging.getLogger(__name__)

@yahoo_bp.route('/update-prices', methods=['POST'])
def update_prices():
    """Direct CMP update from Yahoo Finance for admin_trade_signals table"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import yfinance as yf
        
        request_data = request.get_json() or {}
        direct_update = request_data.get('direct_update', False)
        
        logger.info("Starting Yahoo Finance direct CMP update for admin_trade_signals table")
        
        # Database connection
        DATABASE_URL = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"
        
        def get_yahoo_price(symbol):
            """Get live price from Yahoo Finance with retry logic"""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    yf_symbol = symbol + ".NS"
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        return float(round(price, 2))
                    return None
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Yahoo Finance attempt {attempt + 1} failed for {symbol}: {e}, retrying...")
                        time.sleep(5 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Yahoo Finance error for {symbol} after {max_retries} attempts: {e}")
                        return None
        
        updated_count = 0
        errors = []
        start_time = datetime.utcnow()
        
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all unique symbols from admin_trade_signals
                cursor.execute("""
                    SELECT DISTINCT 
                        COALESCE(symbol, etf) as etf_symbol,
                        COUNT(*) as record_count
                    FROM admin_trade_signals 
                    WHERE COALESCE(symbol, etf) IS NOT NULL AND COALESCE(symbol, etf) != ''
                    GROUP BY COALESCE(symbol, etf)
                """)
                
                symbol_data = cursor.fetchall()
                symbols = [row['etf_symbol'] for row in symbol_data]
                
                logger.info(f"Found {len(symbols)} unique symbols to update: {symbols}")
                
                results = {}
                total_records_updated = 0
                
                for symbol in symbols:
                    try:
                        logger.info(f"Processing {symbol} via Yahoo Finance...")
                        price = get_yahoo_price(symbol)
                        
                        if price and price > 0:
                            # Update all records with this symbol
                            cursor.execute("""
                                UPDATE admin_trade_signals 
                                SET cmp = %s
                                WHERE (symbol = %s OR etf = %s)
                                AND (cmp IS NULL OR cmp != %s)
                            """, (price, symbol, symbol, price))
                            
                            rows_updated = cursor.rowcount
                            total_records_updated += rows_updated
                            updated_count += 1
                            
                            results[symbol] = {
                                'success': True,
                                'price': price,
                                'rows_updated': rows_updated
                            }
                            
                            logger.info(f"✓ Updated {rows_updated} records for {symbol}: ₹{price}")
                        else:
                            results[symbol] = {
                                'success': False,
                                'error': 'Could not fetch price'
                            }
                            errors.append(f"Failed to fetch price for {symbol}")
                            logger.warning(f"⚠️ Could not fetch price for {symbol}")
                        
                        # Rate limiting - increase delay to avoid 429 errors
                        time.sleep(2)
                        
                    except Exception as e:
                        error_msg = f"Error updating {symbol}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        results[symbol] = {
                            'success': False,
                            'error': str(e)
                        }
                
                conn.commit()
                duration = (datetime.utcnow() - start_time).total_seconds()
                
        logger.info(f"✅ Yahoo Finance CMP update completed!")
        logger.info(f"   • Total symbols processed: {len(symbols)}")
        logger.info(f"   • Successful updates: {updated_count}")
        logger.info(f"   • Database rows updated: {total_records_updated}")
        logger.info(f"   • Errors: {len(errors)}")
        logger.info(f"   • Duration: {duration:.2f} seconds")
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated CMP for {updated_count}/{len(symbols)} symbols',
            'total_symbols': len(symbols),
            'successful_updates': updated_count,
            'updated_count': total_records_updated,
            'failed_updates': len(errors),
            'errors': errors,
            'results': results,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'Yahoo Finance',
            'direct_update': True
        })
        
    except Exception as e:
        logger.error(f"Error in Yahoo Finance direct CMP update: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update CMP from Yahoo Finance'
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
