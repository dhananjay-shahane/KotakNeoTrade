# Updated Yahoo Finance API code to dynamically determine the symbol suffix.
from flask import Blueprint, request, jsonify
import logging
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import yfinance as yf

yahoo_bp = Blueprint('yahoo', __name__, url_prefix='/api/yahoo')
logger = logging.getLogger(__name__)

def get_yahoo_symbol_suffix(symbol):
    """Determine the appropriate Yahoo Finance symbol suffix."""
    # This is a placeholder; replace with your actual logic to determine
    # the suffix based on the symbol and/or exchange.
    # For example, you might check a database or use a naming convention.
    # For now, it defaults to ".NS"

    # Example logic (replace this with your actual implementation):
    if symbol.startswith("SBIN"):
        return "SBIN.NS"
    elif symbol.startswith("INFY"):
        return "INFY.NS"
    else:
        return symbol + ".NS" # Default to NSE

def get_live_price(symbol):
    """Get live CMP using Yahoo Finance with dynamic suffix"""
    try:
        yf_symbol = get_yahoo_symbol_suffix(symbol)
        logger.info(f"🔄 Fetching price for {symbol} -> {yf_symbol}")

        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1d")

        if not hist.empty:
            price = hist['Close'].iloc[-1]
            price_float = float(round(price, 2))
            logger.info(f"✅ Got price for {symbol}: ₹{price_float}")
            return price_float
        else:
            logger.warning(f"❌ No price data found for {symbol}")
            return None

    except Exception as e:
        logger.error(f"❌ Error fetching price for {symbol}: {e}")
        return None

@yahoo_bp.route('/update-prices', methods=['POST', 'GET'])
def update_prices():
    """Update CMP for admin_trade_signals table using Yahoo Finance"""
    try:
        logger.info("🚀 Starting Yahoo Finance CMP update for admin_trade_signals table")

        # External database connection
        external_db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }

        updated_count = 0
        errors = []
        start_time = time.time()
        results = {}
        total_records_updated = 0

        try:
            conn = psycopg2.connect(**external_db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

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

            for i, symbol in enumerate(symbols, 1):
                try:
                    logger.info(f"🔄 Processing {i}/{len(symbols)}: {symbol} via Yahoo Finance...")

                    # Fetch live price using the working function
                    price = get_live_price(symbol)

                    if price and price > 0:
                        # Update all records with this symbol in external database
                        update_query = """
                            UPDATE admin_trade_signals 
                            SET cmp = %s
                            WHERE (symbol = %s OR etf = %s)
                        """
                        cursor.execute(update_query, (float(price), symbol, symbol))

                        rows_updated = cursor.rowcount
                        total_records_updated += rows_updated
                        updated_count += 1

                        logger.info(f"✅ Updated {rows_updated} records for {symbol}: ₹{price}")

                        results[symbol] = {
                            'success': True,
                            'price': float(price),
                            'rows_updated': rows_updated,
                            'timestamp': datetime.now().isoformat(),
                            'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
                        }
                    else:
                        results[symbol] = {
                            'success': False,
                            'error': 'Could not fetch price from Yahoo Finance',
                            'timestamp': datetime.now().isoformat(),
                            'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
                        }
                        errors.append(f"Failed to fetch price for {symbol}")
                        logger.warning(f"⚠️ Could not fetch price for {symbol}")

                    # Add delay to avoid rate limiting
                    time.sleep(2)

                except Exception as e:
                    error_msg = f"Error updating {symbol}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    results[symbol] = {
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
                    }

            conn.commit()
            duration = time.time() - start_time

        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            return jsonify({
                'success': False,
                'error': f'Database connection failed: {str(db_error)}',
                'message': 'Failed to connect to database'
            }), 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

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
            'timestamp': datetime.now().isoformat(),
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
        price = get_live_price(symbol)

        if price:
            return jsonify({
                'success': True,
                'data': {
                    'symbol': symbol,
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'No price data found for {symbol}',
                'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
            }), 404

    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@yahoo_bp.route('/test-symbol/<symbol>', methods=['GET'])
def test_symbol_price(symbol):
    """Test price fetching for a specific symbol with detailed logging"""
    try:
        logger.info(f"🧪 Testing price fetch for symbol: {symbol}")

        # Test the working function
        price = get_live_price(symbol)

        return jsonify({
            'success': True if price else False,
            'symbol': symbol,
            'price': price,
            'yahoo_symbol': f"{symbol}.NS",
            'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/",
            'timestamp': datetime.now().isoformat(),
            'message': f'Successfully fetched price: ₹{price}' if price else 'Failed to fetch price'
        })

    except Exception as e:
        logger.error(f"Error testing price for {symbol}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'symbol': symbol,
            'yahoo_url': f"https://finance.yahoo.com/quote/{get_yahoo_symbol_suffix(symbol)}/"
        }), 500

@yahoo_bp.route('/status', methods=['GET'])
def get_status():
    """Get Yahoo Finance service status"""
    try:
        return jsonify({
            'success': True,
            'service': 'Yahoo Finance',
            'status': 'active',
            'timestamp': datetime.now().isoformat(),
            'api_endpoint': '/api/yahoo/update-prices',
            'test_endpoint': '/api/yahoo/test-symbol/<symbol>'
        })

    except Exception as e:
        logger.error(f"Error getting Yahoo Finance status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
`