"""
User Deals Service for fetching data from user_deals table
Connects to external PostgreSQL database and provides user deals with real-time CMP from symbols schema
"""

import psycopg2
import psycopg2.extras
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class UserDealsService:
    """Service for connecting to external PostgreSQL database for user deals"""

    def __init__(self):
        self.db_config = {
            'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
            'database': "kotak_trading_db",
            'user': "kotak_trading_db_user",
            'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
            'port': 5432
        }
        self.connection = None

    def connect(self):
        """Establish connection to external database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✓ Connected to external PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to external database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✓ Disconnected from external database")

    def get_user_deals_with_cmp(self) -> List[Dict]:
        """Fetch user deals from user_deals table and get CMP from symbols schema"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            with self.connection.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First, check what tables exist in both public and symbols schemas
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                public_tables = [
                    row['table_name'] for row in cursor.fetchall()
                ]
                logger.info(f"Available public tables: {public_tables}")

                # Check symbols schema for symbol tables
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'symbols' AND table_type = 'BASE TABLE'"
                )
                symbol_tables = [
                    row['table_name'] for row in cursor.fetchall()
                ]
                logger.info(
                    f"Available symbol tables in symbols schema: {symbol_tables}"
                )

                # Check if user_deals table exists and has data
                if 'user_deals' in public_tables:
                    cursor.execute("SELECT COUNT(*) as count FROM user_deals")
                    row_count = cursor.fetchone()['count']
                    logger.info(f"user_deals table has {row_count} rows")

                    if row_count == 0:
                        logger.info("No user deals found in database")
                        return []

                    # Query to get required fields from user_deals table
                    query = """
                    SELECT 
                        id,
                        symbol,
                        entry_date,
                        position_type,
                        quantity,
                        entry_price,
                        current_price,
                        target_price,
                        stop_loss,
                        invested_amount,
                        current_value,
                        pnl_amount,
                        pnl_percent,
                        status,
                        deal_type,
                        notes,
                        tags,
                        created_at,
                        updated_at,
                        pos,
                        qty,
                        ep,
                        cmp,
                        tp,
                        inv,
                        pl
                    FROM user_deals 
                    WHERE symbol IS NOT NULL AND symbol != ''
                    ORDER BY created_at DESC
                    """

                    cursor.execute(query)
                    results = cursor.fetchall()

                    # Use symbol tables from symbols schema for price matching
                    logger.info(f"Found {len(symbol_tables)} symbol tables in symbols schema: {symbol_tables[:10]}...")  # Show first 10

                    # Convert RealDictRow to regular dict and handle data types
                    deals = []
                    for row in results:
                        deal = dict(row)
                        
                        # Handle symbol field conversion
                        if deal.get('symbol'):
                            deal['symbol'] = str(deal['symbol']).upper()
                        else:
                            deal['symbol'] = ''

                        # Set pos to 0 if deal is closed
                        deal_status = str(deal.get('status', 'ACTIVE')).upper()
                        if deal_status == 'CLOSED':
                            deal['pos'] = '0'

                        # Set default CMP if not available
                        if not deal.get('cmp'):
                            deal['cmp'] = 0.0

                        # Try to get CMP from matching symbol table in symbols schema
                        symbol_name = deal.get('symbol', '').upper()
                        if symbol_name and symbol_tables:
                            # Look for matching table (case-insensitive, multiple matching strategies)
                            matching_table = None
                            
                            # Strategy 1: Exact match with symbol name + _5m
                            exact_match = f"{symbol_name}_5m".lower()
                            for table in symbol_tables:
                                if table.lower() == exact_match:
                                    matching_table = table
                                    break
                            
                            # Strategy 2: Table contains symbol name
                            if not matching_table:
                                for table in symbol_tables:
                                    if symbol_name.lower() in table.lower():
                                        matching_table = table
                                        break
                            
                            # Strategy 3: Symbol name contains table name (for shorter table names)
                            if not matching_table:
                                for table in symbol_tables:
                                    table_base = table.replace('_5m', '').replace('_', '')
                                    if table_base.upper() in symbol_name.upper():
                                        matching_table = table
                                        break
                            
                            if matching_table:
                                try:
                                    # Get the latest price data from the matching table in symbols schema
                                    # Use the structure: datetime, open, high, low, close, volume
                                    price_query = f"""
                                    SELECT datetime, open, high, low, close, volume 
                                    FROM symbols."{matching_table}" 
                                    ORDER BY datetime DESC
                                    LIMIT 1
                                    """
                                    cursor.execute(price_query)
                                    price_data = cursor.fetchone()
                                    
                                    if price_data:
                                        # Use close price as CMP
                                        close_price = price_data['close'] if isinstance(price_data, dict) else price_data[4]
                                        if close_price:
                                            deal['cmp'] = round(float(close_price), 2)
                                            deal['current_price'] = deal['cmp']  # Update current_price as well
                                            logger.info(f"Updated CMP for {symbol_name} from symbols.{matching_table}: {deal['cmp']}")
                                        else:
                                            logger.warning(f"No valid close price found in symbols.{matching_table} for {symbol_name}")
                                    else:
                                        logger.warning(f"No price data found in symbols.{matching_table} for {symbol_name}")
                                        
                                except Exception as e:
                                    logger.error(f"Error fetching price for {symbol_name} from symbols.{matching_table}: {e}")
                            else:
                                logger.info(f"No matching symbol table found for {symbol_name} among {len(symbol_tables)} symbol tables in symbols schema")

                        # Calculate metrics if we have the basic data
                        if deal.get('quantity') and deal.get('entry_price'):
                            quantity = float(deal.get('quantity', 0))
                            entry_price = float(deal.get('entry_price', 0))
                            current_price = float(deal.get('cmp', 0))
                            
                            # Calculate invested amount
                            if not deal.get('invested_amount'):
                                deal['invested_amount'] = round(quantity * entry_price, 2)
                            
                            # Calculate current value
                            if current_price > 0:
                                deal['current_value'] = round(quantity * current_price, 2)
                                
                                # Calculate PnL
                                pnl_amount = deal['current_value'] - deal['invested_amount']
                                deal['pnl_amount'] = round(pnl_amount, 2)
                                
                                # Calculate PnL percentage
                                if deal['invested_amount'] > 0:
                                    deal['pnl_percent'] = round((pnl_amount / deal['invested_amount']) * 100, 2)
                                else:
                                    deal['pnl_percent'] = 0.0
                            else:
                                deal['current_value'] = deal['invested_amount']
                                deal['pnl_amount'] = 0.0
                                deal['pnl_percent'] = 0.0

                        deals.append(deal)

                    logger.info(f"✓ Fetched {len(deals)} user deals with CMP from database")
                    return deals
                else:
                    logger.error("user_deals table not found in database")
                    return []

        except Exception as e:
            logger.error(f"Error fetching user deals: {e}")
            return []

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Global service instance
user_deals_service = UserDealsService()

def get_user_deals_data():
    """Function to get user deals data with CMP from symbols schema"""
    try:
        with user_deals_service as service:
            return service.get_user_deals_with_cmp()
    except Exception as e:
        logger.error(f"Error getting user deals data: {e}")
        return []