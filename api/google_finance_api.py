
"""Google Finance API for live CMP updates"""
from flask import Blueprint, request, jsonify
import logging
import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

google_finance_bp = Blueprint('google_finance', __name__, url_prefix='/api/google-finance')
logger = logging.getLogger(__name__)

# Database connection string
DATABASE_URL = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"

def get_google_finance_price(symbol: str) -> Optional[float]:
    """Fetch live price from Google Finance with enhanced error handling"""
    try:
        url = f"https://www.google.com/finance/quote/{symbol.upper()}:NSE"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Add session for better connection handling
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors for Google Finance price
            price_selectors = [
                "div[class*='YMlKec fxKbKc']",
                "div[class*='YMlKec']", 
                "div[data-source='SPYlIb']",
                "span[class*='IsqQVc NprOob XcVN5d']",
                "div[jsname='ip75Cb']",
                "c-wiz[data-node-index] div[class*='kf1m0']"
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text().strip()
                    # Clean the price text more thoroughly
                    price_text = price_text.replace("₹", "").replace(",", "").replace("$", "").replace(" ", "")
                    try:
                        price = float(price_text)
                        if price > 0:  # Ensure price is valid
                            logger.info(f"✅ Google Finance price for {symbol}: ₹{price}")
                            return price
                    except (ValueError, TypeError):
                        continue
        
        logger.warning(f"⚠️ Google Finance: No valid price found for {symbol} (Status: {response.status_code})")
        return None
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Google Finance timeout for {symbol}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Google Finance connection error for {symbol}")
        return None
    except Exception as e:
        logger.error(f"❌ Google Finance error for {symbol}: {e}")
        return None

@google_finance_bp.route('/live-price/<symbol>', methods=['GET'])
def get_live_price(symbol):
    """Get live price for a single symbol from Google Finance"""
    try:
        price = get_google_finance_price(symbol)
        if price:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'price': price,
                'source': 'Google Finance'
            })
        else:
            return jsonify({
                'success': False,
                'symbol': symbol,
                'error': 'Could not fetch price'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_finance_bp.route('/update-prices', methods=['POST'])
def update_prices():
    """Update CMP for all ETF symbols in admin_trade_signals table"""
    try:
        # Import the Google Finance CMP updater
        from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater
        
        logger.info("Starting Google Finance CMP update via API")
        
        # Create updater instance
        updater = GoogleFinanceCMPUpdater()
        
        # Update all symbols
        result = updater.update_all_symbols()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'updated_count': result['updated_count'],
                'total_symbols': result.get('total_symbols', 0),
                'successful_symbols': result.get('successful_symbols', 0),
                'error_count': result['error_count'],
                'duration': result.get('duration', 0),
                'data_source': 'Google Finance'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Update failed'),
                'data_source': 'Google Finance'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in Google Finance update: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update prices from Google Finance'
        }), 500

@google_finance_bp.route('/update-etf-cmp', methods=['POST'])
def update_etf_cmp():
    """Direct CMP update endpoint for admin_trade_signals table"""
    try:
        request_data = request.get_json() or {}
        direct_update = request_data.get('direct_update', False)
        
        logger.info("Starting Google Finance direct CMP update for admin_trade_signals table")
        
        updated_count = 0
        errors = []
        start_time = time.time()
        
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
                        logger.info(f"Processing {symbol}...")
                        price = get_google_finance_price(symbol)
                        
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
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        error_msg = f"Error updating {symbol}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        results[symbol] = {
                            'success': False,
                            'error': str(e)
                        }
                
                conn.commit()
                duration = time.time() - start_time
                
        logger.info(f"✅ Google Finance CMP update completed!")
        logger.info(f"   • Total symbols processed: {len(symbols)}")
        logger.info(f"   • Successful updates: {updated_count}")
        logger.info(f"   • Database rows updated: {total_records_updated}")
        logger.info(f"   • Errors: {len(errors)}")
        logger.info(f"   • Duration: {duration:.2f} seconds")
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated CMP for {updated_count}/{len(symbols)} symbols',
            'symbols_processed': len(symbols),
            'updated_count': total_records_updated,
            'successful_updates': updated_count,
            'errors': errors,
            'results': results,
            'duration': duration,
            'data_source': 'Google Finance',
            'direct_update': True
        })
        
    except Exception as e:
        logger.error(f"Error in direct Google Finance CMP update: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update CMP from Google Finance'
        }), 500

@google_finance_bp.route('/update-etf-cmp-legacy', methods=['POST'])
def update_etf_cmp_legacy():
    """Update CMP for all ETF symbols in admin_trade_signals table (legacy method)"""
    try:
        updated_count = 0
        errors = []
        
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all unique symbols
                cursor.execute("""
                    SELECT DISTINCT symbol as etf_symbol FROM admin_trade_signals 
                    WHERE symbol IS NOT NULL AND symbol != ''
                    UNION
                    SELECT DISTINCT etf as etf_symbol FROM admin_trade_signals 
                    WHERE etf IS NOT NULL AND etf != ''
                """)
                
                symbols = [row['etf_symbol'] for row in cursor.fetchall()]
                logger.info(f"Updating CMP for {len(symbols)} symbols: {symbols}")
                
                results = {}
                
                for symbol in symbols:
                    try:
                        price = get_google_finance_price(symbol)
                        
                        if price and price > 0:
                            # Update database
                            cursor.execute("""
                                UPDATE admin_trade_signals 
                                SET cmp = %s
                                WHERE (symbol = %s OR etf = %s)
                            """, (price, symbol, symbol))
                            
                            rows_updated = cursor.rowcount
                            updated_count += rows_updated
                            
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
                        
                        # Small delay to avoid rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        error_msg = f"Error updating {symbol}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        results[symbol] = {
                            'success': False,
                            'error': str(e)
                        }
                
                conn.commit()
                
        return jsonify({
            'success': True,
            'message': f'Updated CMP for {updated_count} records',
            'symbols_processed': len(symbols),
            'updated_count': updated_count,
            'errors': errors,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error updating ETF CMP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@google_finance_bp.route('/bulk-prices', methods=['POST'])
def get_bulk_prices():
    """Get live prices for multiple symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        results = {}
        
        for symbol in symbols:
            price = get_google_finance_price(symbol)
            results[symbol] = {
                'price': price,
                'success': price is not None
            }
            time.sleep(0.5)  # Rate limiting
        
        return jsonify({
            'success': True,
            'results': results,
            'source': 'Google Finance'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
