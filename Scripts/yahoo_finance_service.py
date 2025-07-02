
import yfinance as yf
import logging
from datetime import datetime
from decimal import Decimal
import time
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class YahooFinanceService:
    def __init__(self):
        self.session = None
        # Database connection string
        self.db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
    
    def get_stock_price(self, symbol):
        """Fetch current price for a single symbol from Yahoo Finance with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Add .NS suffix for NSE stocks if not already present
                yahoo_symbol = symbol
                if not yahoo_symbol.endswith('.NS') and not yahoo_symbol.endswith('.BO'):
                    yahoo_symbol = f"{symbol}.NS"
                
                logger.info(f"Fetching price for {symbol} -> {yahoo_symbol} (Attempt {attempt + 1}/{max_retries})")
                
                ticker = yf.Ticker(yahoo_symbol)
                
                # Try multiple methods to get price data
                price_data = None
            
            # Method 1: Try recent history (most reliable)
            try:
                hist = ticker.history(period="5d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    open_price = float(hist['Open'].iloc[-1]) if not hist['Open'].empty else None
                    high_price = float(hist['High'].iloc[-1]) if not hist['High'].empty else None
                    low_price = float(hist['Low'].iloc[-1]) if not hist['Low'].empty else None
                    volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else None
                    
                    price_data = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'open_price': open_price,
                        'high_price': high_price,
                        'low_price': low_price,
                        'volume': volume,
                        'previous_close': current_price,  # Use current as previous for now
                        'change_amount': 0,
                        'change_percent': 0,
                        'timestamp': datetime.utcnow()
                    }
                    logger.info(f"✅ Got price from history for {symbol}: ₹{current_price}")
                    return price_data
            except Exception as e:
                logger.warning(f"History method failed for {symbol}: {e}")
            
            # Method 2: Try info dict
            try:
                info = ticker.info
                if info:
                    current_price = (info.get('currentPrice') or 
                                   info.get('regularMarketPrice') or 
                                   info.get('previousClose'))
                    
                    if current_price:
                        open_price = info.get('regularMarketOpen') or info.get('open')
                        high_price = info.get('regularMarketDayHigh') or info.get('dayHigh')
                        low_price = info.get('regularMarketDayLow') or info.get('dayLow')
                        volume = info.get('regularMarketVolume') or info.get('volume')
                        previous_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
                        
                        # Calculate change
                        change_amount = 0
                        change_percent = 0
                        if previous_close and current_price:
                            change_amount = float(current_price) - float(previous_close)
                            change_percent = (change_amount / float(previous_close)) * 100
                        
                        price_data = {
                            'symbol': symbol,
                            'current_price': float(current_price),
                            'open_price': float(open_price) if open_price else None,
                            'high_price': float(high_price) if high_price else None,
                            'low_price': float(low_price) if low_price else None,
                            'volume': int(volume) if volume else None,
                            'change_amount': change_amount,
                            'change_percent': change_percent,
                            'previous_close': float(previous_close) if previous_close else None,
                            'timestamp': datetime.utcnow()
                        }
                        logger.info(f"✅ Got price from info for {symbol}: ₹{current_price}")
                        return price_data
            except Exception as e:
                logger.warning(f"Info method failed for {symbol}: {e}")
            
            logger.warning(f"⚠️ No price data found for {symbol} on attempt {attempt + 1}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Failed to get price for {symbol} after {max_retries} attempts")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error fetching price for {symbol} (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"❌ Failed to get price for {symbol} after {max_retries} attempts")
                    return None
        
        return None
    
    def get_multiple_prices(self, symbols):
        """Fetch prices for multiple symbols with rate limiting"""
        prices = {}
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
            price_data = self.get_stock_price(symbol)
            if price_data:
                prices[symbol] = price_data
            # Rate limiting - sleep between requests
            time.sleep(1)  # Increased delay to avoid rate limiting
        return prices
    
    def update_admin_signals_prices(self):
        """Update current prices in admin_trade_signals table using direct DB connection"""
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all symbols that need updating
            cursor.execute("SELECT DISTINCT symbol FROM admin_trade_signals WHERE symbol IS NOT NULL;")
            symbol_rows = cursor.fetchall()
            
            if not symbol_rows:
                logger.info("No symbols to update")
                return 0
            
            symbols = [row['symbol'] for row in symbol_rows]
            logger.info(f"Updating prices for {len(symbols)} symbols: {symbols}")
            
            # Get prices from Yahoo Finance
            prices = self.get_multiple_prices(symbols)
            
            updated_count = 0
            for symbol, price_data in prices.items():
                try:
                    # Update all records with this symbol
                    update_query = """
                        UPDATE admin_trade_signals 
                        SET cmp = %s, last_update_time = %s 
                        WHERE symbol = %s
                    """
                    cursor.execute(update_query, (
                        Decimal(str(price_data['current_price'])),
                        datetime.utcnow(),
                        symbol
                    ))
                    
                    rows_updated = cursor.rowcount
                    updated_count += rows_updated
                    
                    logger.info(f"✅ Updated {rows_updated} records for {symbol}: ₹{price_data['current_price']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating {symbol}: {e}")
                    continue
            
            # Commit all updates
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Successfully updated {updated_count} records with Yahoo Finance data")
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Error updating admin signals prices: {str(e)}")
            return 0
    
    def update_realtime_quotes(self):
        """Update realtime_quotes table with Yahoo Finance data"""
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get unique symbols from admin signals
            cursor.execute("SELECT DISTINCT symbol FROM admin_trade_signals WHERE symbol IS NOT NULL;")
            symbol_rows = cursor.fetchall()
            
            if not symbol_rows:
                logger.info("No symbols to update in realtime quotes")
                return 0
            
            symbols = [row['symbol'] for row in symbol_rows]
            
            # Get prices from Yahoo Finance
            prices = self.get_multiple_prices(symbols)
            
            updated_count = 0
            for symbol, price_data in prices.items():
                try:
                    # Check if quote exists
                    cursor.execute("SELECT id FROM realtime_quotes WHERE symbol = %s", (symbol,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing quote
                        update_query = """
                            UPDATE realtime_quotes 
                            SET current_price = %s, open_price = %s, high_price = %s, 
                                low_price = %s, close_price = %s, change_amount = %s, 
                                change_percent = %s, volume = %s, timestamp = %s, 
                                data_source = %s, fetch_status = %s
                            WHERE symbol = %s
                        """
                        cursor.execute(update_query, (
                            Decimal(str(price_data['current_price'])),
                            Decimal(str(price_data['open_price'])) if price_data['open_price'] else None,
                            Decimal(str(price_data['high_price'])) if price_data['high_price'] else None,
                            Decimal(str(price_data['low_price'])) if price_data['low_price'] else None,
                            Decimal(str(price_data['previous_close'])) if price_data['previous_close'] else None,
                            Decimal(str(price_data['change_amount'])),
                            Decimal(str(price_data['change_percent'])),
                            price_data['volume'],
                            datetime.utcnow(),
                            'YAHOO_FINANCE',
                            'SUCCESS',
                            symbol
                        ))
                    else:
                        # Insert new quote
                        insert_query = """
                            INSERT INTO realtime_quotes 
                            (symbol, current_price, open_price, high_price, low_price, 
                             close_price, change_amount, change_percent, volume, timestamp, 
                             data_source, fetch_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            symbol,
                            Decimal(str(price_data['current_price'])),
                            Decimal(str(price_data['open_price'])) if price_data['open_price'] else None,
                            Decimal(str(price_data['high_price'])) if price_data['high_price'] else None,
                            Decimal(str(price_data['low_price'])) if price_data['low_price'] else None,
                            Decimal(str(price_data['previous_close'])) if price_data['previous_close'] else None,
                            Decimal(str(price_data['change_amount'])),
                            Decimal(str(price_data['change_percent'])),
                            price_data['volume'],
                            datetime.utcnow(),
                            'YAHOO_FINANCE',
                            'SUCCESS'
                        ))
                    
                    updated_count += 1
                    logger.info(f"✅ Updated quote for {symbol}: ₹{price_data['current_price']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating quote for {symbol}: {e}")
                    continue
            
            # Commit all updates
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Successfully updated {updated_count} realtime quotes with Yahoo Finance data")
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Error updating realtime quotes: {str(e)}")
            return 0

# Global service instance
yahoo_service = YahooFinanceService()
