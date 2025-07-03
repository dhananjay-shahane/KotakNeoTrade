#!/usr/bin/env python3
"""
Google Finance CMP Updater - External script for updating admin_trade_signals table
Uses Google Finance data via yfinance to dynamically update CMP values for every trade
Can be run independently as a standalone script or scheduled as a cron job
"""

import os
import sys
import logging
import time
import random
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import yfinance as yf
import requests
from typing import Dict, List, Optional, Tuple
import concurrent.futures
from threading import Lock

# Install required packages if not available
try:
    from bs4 import BeautifulSoup
except ImportError:
    logging.warning("BeautifulSoup not available - using fallback prices only")
    BeautifulSoup = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cmp_updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class GoogleFinanceCMPUpdater:
    """Google Finance CMP Updater for admin_trade_signals table"""
    
    def __init__(self):
        """Initialize with external database configuration"""
        self.db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
        self.updated_count = 0
        self.error_count = 0
        self.lock = Lock()  # Thread lock for shared counters

    def _process_single_symbol(self, symbol: str) -> Dict:
        """Process a single symbol and return result (for parallel execution)"""
        try:
            # First try to get comprehensive historical data
            historical_data = self.fetch_historical_data(symbol)
            
            if historical_data:
                # Update database with historical data
                updated_rows = self.update_symbol_with_historical_data(symbol, historical_data)
                return {
                    'price': historical_data.get('cmp'),
                    'updated_rows': updated_rows,
                    'status': 'success',
                    'historical_data': historical_data
                }
            else:
                # Fallback to simple price update
                # Try Google Finance first
                live_price = self.fetch_google_finance_price(symbol)

                # If Google Finance fails, try yfinance as fallback
                if not live_price or live_price <= 0:
                    live_price = self.fetch_live_price_yfinance(symbol)

                if live_price and live_price > 0:
                    # Update database
                    updated_rows = self.update_symbol_cmp(symbol, live_price)
                    return {
                        'price': live_price,
                        'updated_rows': updated_rows,
                        'status': 'success'
                    }
                else:
                    return {
                        'price': None,
                        'updated_rows': 0,
                        'status': 'failed'
                    }
        except Exception as e:
            logging.error(f"❌ Error processing {symbol}: {e}")
            return {
                'price': None,
                'updated_rows': 0,
                'status': 'failed',
                'error': str(e)
            }

    def fetch_google_finance_price(self, symbol: str) -> Optional[float]:
        """Fetch live price from Google Finance with enhanced error handling"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            clean_symbol = symbol.strip().upper()
            
            # Try different exchange suffixes for Google Finance
            exchanges = ['NSE', 'BSE']  # Try NSE first, then BSE
            
            for exchange in exchanges:
                url = f"https://www.google.com/finance/quote/{clean_symbol}:{exchange}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                try:
                    logging.info(f"Trying Google Finance: {url}")
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Try multiple selectors for price
                        price_selectors = [
                            "div[class*='YMlKec fxKbKc']",
                            "div[class*='YMlKec']",
                            "span[class*='IsqQVc NprOob XcVN5d']",
                            "div[jsname='ip75Cb']"
                        ]
                        
                        for selector in price_selectors:
                            price_element = soup.select_one(selector)
                            if price_element:
                                price_text = price_element.get_text().strip()
                                price_text = price_text.replace("₹", "").replace(",", "").replace("$", "").strip()
                                try:
                                    price = float(price_text)
                                    if price > 0:
                                        logging.info(f"✓ Google Finance live price for {symbol} from {exchange}: ₹{price}")
                                        return price
                                except (ValueError, TypeError):
                                    continue
                    
                    logging.warning(f"⚠️ Google Finance: Could not parse price for {symbol} on {exchange}")
                    
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    logging.warning(f"⚠️ Google Finance network error for {symbol} on {exchange}: {e}")
                    continue
            
            # No fallback data - return None if no authentic price source available

        except Exception as e:
            logging.error(f"❌ Google Finance price fetch failed for {symbol}: {e}")
            return None

    def fetch_live_price_yfinance(self, symbol: str) -> Optional[float]:
        """Fetch live price using yfinance with enhanced error handling"""
        try:
            yahoo_symbol = self.get_yahoo_symbol(symbol)
            logging.info(f"Fetching price for {symbol} -> {yahoo_symbol}")

            # Create ticker object
            ticker = yf.Ticker(yahoo_symbol)

            # Method 1: Try history for last few days (most reliable)
            try:
                hist = ticker.history(period="5d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if price and price > 0:
                        logging.info(f"✓ History price for {symbol}: ₹{price}")
                        return float(price)
            except Exception as e:
                logging.warning(f"History method failed for {symbol}: {e}")

            # Method 2: Try info dict (less reliable but sometimes works)
            try:
                info = ticker.info
                if info:
                    price = (info.get('regularMarketPrice') or 
                            info.get('currentPrice') or 
                            info.get('previousClose') or
                            info.get('lastPrice'))
                    if price and price > 0:
                        logging.info(f"✓ Info price for {symbol}: ₹{price}")
                        return float(price)
            except Exception as e:
                logging.warning(f"Info method failed for {symbol}: {e}")

            # Method 3: Alternative approach - try different period
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    if price and price > 0:
                        logging.info(f"✓ 1d History price for {symbol}: ₹{price}")
                        return float(price)
            except Exception as e:
                logging.warning(f"1d History method failed for {symbol}: {e}")

            logging.warning(f"⚠️ Could not fetch price for {symbol}")
            return None

        except Exception as e:
            logging.error(f"❌ Error fetching price for {symbol}: {e}")
            return None

    def fetch_historical_data(self, symbol: str) -> Dict:
        """Fetch historical price data for performance calculations"""
        try:
            yahoo_symbol = self.get_yahoo_symbol(symbol)
            ticker = yf.Ticker(yahoo_symbol)
            
            # Get 35 days of data to ensure we have 30 trading days
            hist = ticker.history(period="35d")
            
            if hist.empty:
                logging.warning(f"No historical data found for {symbol}")
                return {}
            
            # Get current price (latest close)
            current_price = float(hist['Close'].iloc[-1])
            
            # Calculate 30-day performance
            d30_price = None
            ch30 = 0.0
            
            if len(hist) >= 30:
                d30_price = float(hist['Close'].iloc[-30])
                ch30 = ((current_price - d30_price) / d30_price) * 100
            elif len(hist) >= 20:  # Fallback to 20 days if less than 30
                d30_price = float(hist['Close'].iloc[-20])
                ch30 = ((current_price - d30_price) / d30_price) * 100
            
            # Calculate 7-day performance
            d7_price = None
            ch7 = 0.0
            
            if len(hist) >= 7:
                d7_price = float(hist['Close'].iloc[-7])
                ch7 = ((current_price - d7_price) / d7_price) * 100
            
            result = {
                'cmp': current_price,
                'd30': d30_price or current_price,
                'ch30': round(ch30, 2),
                'd7': d7_price or current_price,
                'ch7': round(ch7, 2),
                'nt': current_price  # Net price (same as current price)
            }
            
            logging.info(f"✓ Historical data for {symbol}: CMP=₹{current_price:.2f}, 30d={ch30:.2f}%, 7d={ch7:.2f}%")
            return result
            
        except Exception as e:
            logging.error(f"❌ Error fetching historical data for {symbol}: {e}")
            return {}
        
    def get_symbols_from_database(self) -> List[str]:
        """Get all unique symbols from admin_trade_signals table"""
        symbols = []

        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get unique symbols from both symbol and etf columns
                    cursor.execute("""
                        SELECT DISTINCT symbol as sym FROM admin_trade_signals 
                        WHERE symbol IS NOT NULL AND symbol != ''
                        UNION
                        SELECT DISTINCT etf as sym FROM admin_trade_signals 
                        WHERE etf IS NOT NULL AND etf != ''
                        ORDER BY sym
                    """)

                    results = cursor.fetchall()
                    symbols = [row['sym'] for row in results if row['sym']]

                    logging.info(f"Found {len(symbols)} unique symbols in database: {symbols}")

        except Exception as e:
            logging.error(f"Error getting symbols from database: {e}")

        return symbols

    def get_yahoo_symbol(self, symbol: str) -> str:
        """Convert Indian stock symbol to Yahoo Finance format"""
        clean_symbol = symbol.strip().upper()
        
        # Add .NS suffix for NSE stocks if not already present
        if not clean_symbol.endswith('.NS') and not clean_symbol.endswith('.BO'):
            return f"{clean_symbol}.NS"
        
        return clean_symbol

    def update_symbol_with_historical_data(self, symbol: str, data: Dict) -> int:
        """Update symbol with comprehensive market data including historical performance"""
        updated_rows = 0

        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # Check which columns exist in admin_trade_signals
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'admin_trade_signals' 
                        AND column_name IN ('updated_at', 'last_update_time', 'thirty', 'dh', 'seven', 'ch')
                    """)
                    existing_columns = [row[0] for row in cursor.fetchall()]

                    # Build dynamic update query based on available columns
                    update_fields = ['cmp = %s']
                    update_values = [data.get('cmp', 0)]

                    # Add performance fields if they exist
                    if 'thirty' in existing_columns:
                        update_fields.append('thirty = %s')
                        update_values.append(data.get('d30', 0))
                    
                    if 'dh' in existing_columns:
                        update_fields.append('dh = %s')
                        update_values.append(f"{data.get('ch30', 0):.2f}%")
                    
                    if 'seven' in existing_columns:
                        update_fields.append('seven = %s')
                        update_values.append(data.get('d7', 0))
                    
                    if 'ch' in existing_columns:
                        update_fields.append('ch = %s')
                        update_values.append(f"{data.get('ch7', 0):.2f}%")
                    
                    # Also update d30, ch30, d7, ch7 if they exist
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'admin_trade_signals' 
                        AND column_name IN ('d30', 'ch30', 'd7', 'ch7')
                    """)
                    performance_columns = [row[0] for row in cursor.fetchall()]
                    
                    if 'd30' in performance_columns:
                        update_fields.append('d30 = %s')
                        update_values.append(data.get('d30', 0))
                    
                    if 'ch30' in performance_columns:
                        update_fields.append('ch30 = %s')
                        update_values.append(f"{data.get('ch30', 0):.2f}%")
                    
                    if 'd7' in performance_columns:
                        update_fields.append('d7 = %s')
                        update_values.append(data.get('d7', 0))
                    
                    if 'ch7' in performance_columns:
                        update_fields.append('ch7 = %s')
                        update_values.append(f"{data.get('ch7', 0):.2f}%")
                        update_values.append(data.get('d30', 0))
                    
                    if 'ch30' in performance_columns:
                        update_fields.append('ch30 = %s')
                        update_values.append(f"{data.get('ch30', 0):.2f}%")
                    
                    if 'd7' in performance_columns:
                        update_fields.append('d7 = %s')
                        update_values.append(data.get('d7', 0))
                    
                    if 'ch7' in performance_columns:
                        update_fields.append('ch7 = %s')
                        update_values.append(f"{data.get('ch7', 0):.2f}%")

                    # Add timestamp field
                    if 'last_update_time' in existing_columns:
                        update_fields.append('last_update_time = CURRENT_TIMESTAMP')
                    elif 'updated_at' in existing_columns:
                        update_fields.append('updated_at = CURRENT_TIMESTAMP')

                    # Add condition values
                    update_values.extend([symbol, symbol, data.get('cmp', 0)])

                    # Execute update
                    query = f"""
                        UPDATE admin_trade_signals 
                        SET {', '.join(update_fields)}
                        WHERE (symbol = %s OR etf = %s)
                        AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                    """
                    
                    cursor.execute(query, update_values)
                    admin_updated_rows = cursor.rowcount

                    # Update user_deals table
                    cursor.execute("""
                        UPDATE user_deals 
                        SET cmp = %s, 
                            current_price = %s,
                            last_price_update = CURRENT_TIMESTAMP
                        WHERE (symbol = %s OR etf_symbol = %s)
                        AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                    """, (data.get('cmp', 0), data.get('cmp', 0), symbol, symbol, data.get('cmp', 0)))

                    user_deals_updated_rows = cursor.rowcount
                    updated_rows = admin_updated_rows + user_deals_updated_rows

                    conn.commit()

                    if updated_rows > 0:
                        logging.info(f"✓ Updated {admin_updated_rows} admin_trade_signals and {user_deals_updated_rows} user_deals records for {symbol}")
                        logging.info(f"  CMP: ₹{data.get('cmp', 0):.2f}, 30d: {data.get('ch30', 0):.2f}%, 7d: {data.get('ch7', 0):.2f}%")
                    else:
                        logging.info(f"• No updates needed for {symbol}")

        except Exception as e:
            logging.error(f"❌ Error updating data for {symbol}: {e}")

        return updated_rows

    def update_symbol_cmp(self, symbol: str, new_cmp: float) -> int:
        """Update CMP for a specific symbol in both admin_trade_signals and user_deals tables"""
        updated_rows = 0

        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # Update admin_trade_signals table
                    # First check if updated_at column exists
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'admin_trade_signals' AND column_name = 'updated_at'
                    """)
                    has_updated_at = cursor.fetchone() is not None

                    # Check if last_update_time column exists
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'admin_trade_signals' AND column_name = 'last_update_time'
                    """)
                    has_last_update_time = cursor.fetchone() is not None

                    if has_last_update_time:
                        cursor.execute("""
                            UPDATE admin_trade_signals 
                            SET cmp = %s, 
                                last_update_time = CURRENT_TIMESTAMP
                            WHERE (symbol = %s OR etf = %s)
                            AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                        """, (new_cmp, symbol, symbol, new_cmp))
                    elif has_updated_at:
                        cursor.execute("""
                            UPDATE admin_trade_signals 
                            SET cmp = %s, 
                                updated_at = CURRENT_TIMESTAMP
                            WHERE (symbol = %s OR etf = %s)
                            AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                        """, (new_cmp, symbol, symbol, new_cmp))
                    else:
                        cursor.execute("""
                            UPDATE admin_trade_signals 
                            SET cmp = %s 
                            WHERE (symbol = %s OR etf = %s)
                            AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                        """, (new_cmp, symbol, symbol, new_cmp))

                    admin_updated_rows = cursor.rowcount

                    # Update user_deals table
                    cursor.execute("""
                        UPDATE user_deals 
                        SET cmp = %s, 
                            current_price = %s,
                            last_price_update = CURRENT_TIMESTAMP
                        WHERE (symbol = %s OR etf_symbol = %s)
                        AND (cmp IS NULL OR ABS(cmp - %s) > 0.01)
                    """, (new_cmp, new_cmp, symbol, symbol, new_cmp))

                    user_deals_updated_rows = cursor.rowcount
                    updated_rows = admin_updated_rows + user_deals_updated_rows

                    conn.commit()

                    if updated_rows > 0:
                        logging.info(f"✓ Updated {admin_updated_rows} admin_trade_signals and {user_deals_updated_rows} user_deals records for {symbol} with CMP: ₹{new_cmp}")
                    else:
                        logging.info(f"• No updates needed for {symbol} (CMP already ₹{new_cmp})")

        except Exception as e:
            logging.error(f"❌ Error updating CMP for {symbol}: {e}")

        return updated_rows

    def update_all_symbols(self) -> Dict[str, any]:
        """Update CMP for all symbols in the database"""
        start_time = time.time()
        self.updated_count = 0
        self.error_count = 0

        logging.info("🚀 Starting CMP update process...")

        # Get all symbols from database
        symbols = self.get_symbols_from_database()

        if not symbols:
            logging.warning("No symbols found in database")
            return {
                'success': False,
                'message': 'No symbols found in database',
                'updated_count': 0,
                'error_count': 0,
                'duration': 0
            }

        success_count = 0
        results = {}

        # Process symbols in parallel for speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self._process_single_symbol, symbol): symbol 
                for symbol in symbols
            }
            
            # Collect results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_symbol), 1):
                symbol = future_to_symbol[future]
                logging.info(f"Processing {i}/{len(symbols)}: {symbol}")
                
                try:
                    result = future.result()
                    results[symbol] = result
                    
                    if result['status'] == 'success':
                        with self.lock:
                            self.updated_count += result['updated_rows']
                            success_count += 1
                    else:
                        with self.lock:
                            self.error_count += 1
                            
                except Exception as e:
                    logging.error(f"❌ Error processing {symbol}: {e}")
                    with self.lock:
                        self.error_count += 1
                    results[symbol] = {
                        'price': None,
                        'updated_rows': 0,
                        'status': 'failed',
                        'error': str(e)
                    }

        duration = time.time() - start_time

        logging.info("✅ CMP update completed!")
        logging.info(f"   • Total symbols processed: {len(symbols)}")
        logging.info(f"   • Successful updates: {success_count}")
        logging.info(f"   • Database rows updated: {self.updated_count}")
        logging.info(f"   • Errors: {self.error_count}")
        logging.info(f"   • Duration: {duration:.2f} seconds")

        return {
            'success': True,
            'message': f'Successfully updated {self.updated_count} records',
            'total_symbols': len(symbols),
            'successful_symbols': success_count,
            'updated_count': self.updated_count,
            'error_count': self.error_count,
            'duration': duration,
            'results': results
        }

    def update_specific_symbols(self, symbols: List[str]) -> Dict[str, any]:
        """Update CMP for specific symbols only"""
        start_time = time.time()
        self.updated_count = 0
        self.error_count = 0

        logging.info(f"🚀 Starting CMP update for specific symbols: {symbols}")

        success_count = 0
        results = {}

        for symbol in symbols:
            logging.info(f"Processing: {symbol}")

            # Try Google Finance first
            live_price = self.fetch_google_finance_price(symbol)

            # If Google Finance fails, try yfinance
            if not live_price or live_price <= 0:
                logging.info(f"Google Finance failed, trying yfinance for {symbol}")
                live_price = self.fetch_live_price_yfinance(symbol)

            # If both fail, try alternative/simulated price
            if not live_price or live_price <= 0:
                logging.info(f"Trying fallback source for {symbol}")
                live_price = self.fetch_alternative_price(symbol)

            if live_price and live_price > 0:
                # Update database
                updated_rows = self.update_symbol_cmp(symbol, live_price)
                self.updated_count += updated_rows
                success_count += 1

                results[symbol] = {
                    'price': live_price,
                    'updated_rows': updated_rows,
                    'status': 'success'
                }
            else:
                self.error_count += 1
                results[symbol] = {
                    'price': None,
                    'updated_rows': 0,
                    'status': 'failed'
                }

            time.sleep(0.5)

        duration = time.time() - start_time

        logging.info("✅ Specific symbols update completed!")
        logging.info(f"   • Symbols processed: {len(symbols)}")
        logging.info(f"   • Successful updates: {success_count}")
        logging.info(f"   • Database rows updated: {self.updated_count}")
        logging.info(f"   • Duration: {duration:.2f} seconds")

        return {
            'success': True,
            'message': f'Successfully updated {self.updated_count} records',
            'symbols_processed': len(symbols),
            'successful_symbols': success_count,
            'updated_count': self.updated_count,
            'error_count': self.error_count,
            'duration': duration,
            'results': results
        }

def main():
    """Main function for standalone execution"""
    print("🚀 Google Finance CMP Updater - Standalone Script")
    print("=" * 60)

    # Initialize updater
    updater = GoogleFinanceCMPUpdater()

    # Check if specific symbols are provided as command line arguments
    if len(sys.argv) > 1:
        symbols = [arg.upper().strip() for arg in sys.argv[1:]]
        print(f"Updating specific symbols: {symbols}")
        result = updater.update_specific_symbols(symbols)
    else:
        print("Updating all symbols from database...")
        result = updater.update_all_symbols()

    # Print results
    print("\n" + "=" * 60)
    print("📊 UPDATE RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    print(f"   Updated Records: {result['updated_count']}")
    print(f"   Errors: {result['error_count']}")
    print(f"   Duration: {result.get('duration', 0):.2f} seconds")

    if 'results' in result:
        print("\n📈 INDIVIDUAL SYMBOL RESULTS:")
        for symbol, data in result['results'].items():
            status = "✅" if data['status'] == 'success' else "❌"
            price = f"₹{data['price']:.2f}" if data['price'] else "N/A"
            print(f"   {status} {symbol}: {price} ({data['updated_rows']} rows updated)")

# Utility functions for integration with main app
def update_all_cmp_data():
    """Function to update all CMP data - can be called from main app"""
    updater = GoogleFinanceCMPUpdater()
    return updater.update_all_symbols()

def update_specific_cmp_data(symbols: List[str]):
    """Function to update specific symbols - can be called from main app"""
    updater = GoogleFinanceCMPUpdater()
    return updater.update_specific_symbols(symbols)

def get_live_price_for_symbol(symbol: str) -> Optional[float]:
    """Get live price for a single symbol"""
    updater = GoogleFinanceCMPUpdater()
    return updater.fetch_live_price_yfinance(symbol)

if __name__ == "__main__":
    main()