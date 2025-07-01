"""
Live CMP Service - Fetch real-time quotes from Kotak Neo API
Updates admin_trade_signals table with live market data
"""
import logging
import os
from typing import Dict, List, Optional
from decimal import Decimal
import json

class LiveCMPService:
    """Service for fetching live CMP data from Kotak Neo API"""
    
    def __init__(self):
        self.client = None
        self.session_data = {}
        self.is_authenticated = False
        
    def initialize_client(self):
        """Initialize Kotak Neo client with stored session"""
        try:
            from neo_api_client import NeoAPI
            
            # Try to load session from environment or stored session
            access_token = os.environ.get('NEO_ACCESS_TOKEN')
            session_token = os.environ.get('NEO_SESSION_TOKEN')
            
            if access_token and session_token:
                self.client = NeoAPI(
                    consumer_key=os.environ.get('NEO_CONSUMER_KEY'),
                    consumer_secret=os.environ.get('NEO_CONSUMER_SECRET'),
                    environment='prod'
                )
                
                # Set session tokens
                self.client.set_session(
                    session_token=session_token,
                    access_token=access_token
                )
                
                self.is_authenticated = True
                logging.info("✓ Kotak Neo client initialized with stored session")
                return True
            else:
                logging.warning("⚠️ No stored Kotak Neo session found")
                return False
                
        except ImportError:
            logging.error("❌ neo-api-client not available")
            return False
        except Exception as e:
            logging.error(f"❌ Failed to initialize Kotak Neo client: {str(e)}")
            return False
    
    def get_live_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live quote for a symbol from Kotak Neo API"""
        if not self.is_authenticated or not self.client:
            logging.warning(f"⚠️ Not authenticated, cannot fetch quote for {symbol}")
            return None
            
        try:
            # Use quotes API to get live data
            response = self.client.quotes(
                instrument_tokens=[symbol],
                quote_type="ltp",  # Last Traded Price
                isIndex=False
            )
            
            if response and 'data' in response and response['data']:
                quote_data = response['data'][0] if isinstance(response['data'], list) else response['data']
                
                # Extract CMP (Current Market Price) or LTP (Last Traded Price)
                cmp = quote_data.get('ltp') or quote_data.get('last_price') or quote_data.get('close')
                
                return {
                    'symbol': symbol,
                    'cmp': float(cmp) if cmp else None,
                    'last_traded_price': float(quote_data.get('ltp', 0)) if quote_data.get('ltp') else None,
                    'volume': quote_data.get('volume', 0),
                    'change': quote_data.get('change', 0),
                    'change_percent': quote_data.get('change_percent', 0),
                    'timestamp': quote_data.get('timestamp'),
                    'exchange': exchange
                }
            else:
                logging.warning(f"⚠️ No quote data received for {symbol}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error fetching quote for {symbol}: {str(e)}")
            return None
    
    def get_bulk_quotes(self, symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict]:
        """Get live quotes for multiple symbols"""
        quotes = {}
        
        if not self.is_authenticated or not self.client:
            logging.warning("⚠️ Not authenticated, cannot fetch bulk quotes")
            return quotes
            
        try:
            # Fetch quotes in batches (Kotak Neo API may have limits)
            batch_size = 10
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i+batch_size]
                
                response = self.client.quotes(
                    instrument_tokens=batch_symbols,
                    quote_type="ltp",
                    isIndex=False
                )
                
                if response and 'data' in response:
                    data = response['data']
                    if isinstance(data, list):
                        for quote_data in data:
                            symbol = quote_data.get('instrument_token') or quote_data.get('symbol')
                            if symbol:
                                cmp = quote_data.get('ltp') or quote_data.get('last_price') or quote_data.get('close')
                                quotes[symbol] = {
                                    'cmp': float(cmp) if cmp else None,
                                    'last_traded_price': float(quote_data.get('ltp', 0)) if quote_data.get('ltp') else None,
                                    'volume': quote_data.get('volume', 0),
                                    'change': quote_data.get('change', 0),
                                    'change_percent': quote_data.get('change_percent', 0),
                                    'timestamp': quote_data.get('timestamp'),
                                    'exchange': exchange
                                }
                    else:
                        # Single quote response
                        symbol = data.get('instrument_token') or data.get('symbol')
                        if symbol:
                            cmp = data.get('ltp') or data.get('last_price') or data.get('close')
                            quotes[symbol] = {
                                'cmp': float(cmp) if cmp else None,
                                'last_traded_price': float(data.get('ltp', 0)) if data.get('ltp') else None,
                                'volume': data.get('volume', 0),
                                'change': data.get('change', 0),
                                'change_percent': data.get('change_percent', 0),
                                'timestamp': data.get('timestamp'),
                                'exchange': exchange
                            }
                            
        except Exception as e:
            logging.error(f"❌ Error fetching bulk quotes: {str(e)}")
            
        return quotes
    
    def update_admin_signals_cmp(self, connection_string: str) -> int:
        """Update admin_trade_signals table with live CMP data"""
        updated_count = 0
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Get all symbols from admin_trade_signals
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get unique symbols that need CMP updates
                    cursor.execute("""
                        SELECT DISTINCT symbol, etf 
                        FROM admin_trade_signals 
                        WHERE symbol IS NOT NULL AND symbol != ''
                    """)
                    symbols_data = cursor.fetchall()
                    
                    if not symbols_data:
                        logging.info("No symbols found to update")
                        return 0
                    
                    # Extract symbols list
                    symbols = [row['symbol'] for row in symbols_data if row['symbol']]
                    etf_symbols = [row['etf'] for row in symbols_data if row['etf']]
                    all_symbols = list(set(symbols + etf_symbols))  # Remove duplicates
                    
                    logging.info(f"Fetching live quotes for {len(all_symbols)} symbols: {all_symbols}")
                    
                    # Get live quotes from Kotak Neo API
                    live_quotes = self.get_bulk_quotes(all_symbols)
                    
                    if not live_quotes:
                        logging.warning("No live quotes received from Kotak Neo API")
                        return 0
                    
                    # Update each record with live CMP
                    for symbol in all_symbols:
                        if symbol in live_quotes:
                            quote_data = live_quotes[symbol]
                            cmp = quote_data.get('cmp')
                            last_traded_price = quote_data.get('last_traded_price')
                            
                            # Use CMP if available, otherwise use last_traded_price
                            update_price = cmp if cmp is not None else last_traded_price
                            
                            if update_price is not None and update_price > 0:
                                # Update records where symbol matches or etf matches
                                cursor.execute("""
                                    UPDATE admin_trade_signals 
                                    SET cmp = %s, 
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE (symbol = %s OR etf = %s)
                                """, (update_price, symbol, symbol))
                                
                                updated_count += cursor.rowcount
                                logging.info(f"✓ Updated {cursor.rowcount} records for {symbol} with CMP: {update_price}")
                    
                    conn.commit()
                    logging.info(f"✓ Successfully updated {updated_count} records with live CMP data")
                    
        except Exception as e:
            logging.error(f"❌ Error updating admin signals CMP: {str(e)}")
            
        return updated_count

def get_live_cmp_for_symbols(symbols: List[str]) -> Dict[str, float]:
    """Standalone function to get live CMP for given symbols"""
    service = LiveCMPService()
    
    if not service.initialize_client():
        logging.warning("Cannot fetch live CMP - authentication required")
        return {}
    
    quotes = service.get_bulk_quotes(symbols)
    
    # Extract just the CMP values
    cmp_data = {}
    for symbol, quote_data in quotes.items():
        cmp = quote_data.get('cmp') or quote_data.get('last_traded_price')
        if cmp is not None:
            cmp_data[symbol] = float(cmp)
    
    return cmp_data

def update_live_cmp():
    """Update live CMP for all admin trade signals"""
    service = LiveCMPService()
    
    if not service.initialize_client():
        logging.warning("Cannot update live CMP - authentication required")
        return 0
    
    connection_string = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"
    
    return service.update_admin_signals_cmp(connection_string)