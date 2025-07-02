
import psycopg2
import time
import pandas as pd
import yfinance as yf
from decimal import Decimal
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL connection details
db_config = {
    'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
    'database': "kotak_trading_db",
    'user': "kotak_trading_db_user",
    'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
    'port': 5432
}

def get_live_price(symbol):
    """Get live CMP using Yahoo Finance with improved error handling"""
    try:
        # Clean symbol and add NSE suffix
        clean_symbol = symbol.strip().upper()
        yf_symbol = f"{clean_symbol}.NS"
        
        logger.info(f"Fetching price for {symbol} -> {yf_symbol}")
        
        ticker = yf.Ticker(yf_symbol)
        
        # Method 1: Try recent history (most reliable)
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                logger.info(f"✅ Got price from history: {symbol} = ₹{price}")
                return round(price, 2)
        except Exception as e:
            logger.warning(f"History method failed for {symbol}: {e}")
        
        # Method 2: Try info dict
        try:
            info = ticker.info
            if info:
                price = (info.get('currentPrice') or 
                        info.get('regularMarketPrice') or 
                        info.get('previousClose'))
                
                if price and price > 0:
                    logger.info(f"✅ Got price from info: {symbol} = ₹{price}")
                    return round(float(price), 2)
        except Exception as e:
            logger.warning(f"Info method failed for {symbol}: {e}")
        
        # Method 3: Try 1-day history as fallback
        try:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                logger.info(f"✅ Got price from 1d history: {symbol} = ₹{price}")
                return round(price, 2)
        except Exception as e:
            logger.warning(f"1d history method failed for {symbol}: {e}")
        
        logger.error(f"❌ No price data found for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching price for {symbol}: {e}")
        return None

def fetch_and_update_cmp():
    """Main function to fetch and update CMP values"""
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        logger.info("🚀 Starting CMP update process...")

        # Get all symbols that need updating
        cursor.execute("SELECT id, symbol, etf FROM admin_trade_signals;")
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No records found to update")
            return

        logger.info(f"Found {len(rows)} records to process")

        # Collect unique symbols
        symbols_to_update = set()
        for row in rows:
            signal_id, symbol, etf = row
            if symbol:
                symbols_to_update.add(symbol.strip().upper())
            if etf:
                symbols_to_update.add(etf.strip().upper())

        logger.info(f"Unique symbols to update: {list(symbols_to_update)}")

        # Fetch prices for all symbols
        price_cache = {}
        for i, symbol in enumerate(symbols_to_update, 1):
            logger.info(f"Processing {i}/{len(symbols_to_update)}: {symbol}")
            
            price = get_live_price(symbol)
            if price is not None:
                price_cache[symbol] = price
                logger.info(f"✅ Cached price for {symbol}: ₹{price}")
            else:
                logger.warning(f"⚠️ Failed to get price for {symbol}")
            
            # Rate limiting - sleep between requests
            time.sleep(2)

        # Update database records
        updated_count = 0
        for row in rows:
            signal_id, symbol, etf = row
            
            # Determine which symbol to use for price lookup
            price_symbol = None
            if symbol and symbol.strip().upper() in price_cache:
                price_symbol = symbol.strip().upper()
            elif etf and etf.strip().upper() in price_cache:
                price_symbol = etf.strip().upper()
            
            if price_symbol and price_symbol in price_cache:
                try:
                    new_price = price_cache[price_symbol]
                    
                    # Update with proper data type conversion
                    update_query = """
                        UPDATE admin_trade_signals 
                        SET cmp = %s, last_update_time = %s 
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (
                        Decimal(str(new_price)),  # Convert to Decimal for PostgreSQL
                        datetime.utcnow(),
                        signal_id
                    ))
                    
                    updated_count += 1
                    logger.info(f"✅ Updated record {signal_id} with {price_symbol}: ₹{new_price}")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating record {signal_id}: {e}")
                    continue

        # Commit all updates
        conn.commit()
        logger.info(f"✅ Successfully updated {updated_count} records")

        # Export updated data to CSV
        try:
            cursor.execute("SELECT * FROM admin_trade_signals ORDER BY id;")
            updated_rows = cursor.fetchall()
            
            # Get column names
            colnames = [desc[0] for desc in cursor.description]
            
            # Create DataFrame and export
            df = pd.DataFrame(updated_rows, columns=colnames)
            csv_filename = f"admin_trade_signals_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_filename, index=False)
            logger.info(f"✅ CSV exported: {csv_filename}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting CSV: {e}")

        # Close database connection
        cursor.close()
        conn.close()
        
        logger.info("🎉 CMP update process completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fetch_and_update_cmp()
