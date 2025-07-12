"""
External Database Service for fetching data from admin_trade_signals table
Connects to external PostgreSQL database and provides ETF signals data

 filename : external_db_service.py


"""

import psycopg2
import psycopg2.extras
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class ExternalDBService:
    """Service for connecting to external PostgreSQL database"""

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

    def get_admin_trade_signals(self) -> List[Dict]:
        """Fetch only required fields from admin_trade_signals and get CMP from available tables"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            with self.connection.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First, check what tables exist and get row count
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = [row['table_name'] for row in cursor.fetchall()]
                logger.info(f"Available tables: {tables}")
                
                # Check if admin_trade_signals table exists and has data
                if 'admin_trade_signals' in tables:
                    cursor.execute("SELECT COUNT(*) as count FROM admin_trade_signals")
                    row_count = cursor.fetchone()['count']
                    logger.info(f"admin_trade_signals table has {row_count} rows")
                    
                    if row_count == 0:
                        logger.warning("admin_trade_signals table is empty - checking table structure")
                        # Check table structure
                        cursor.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = 'admin_trade_signals'
                        """)
                        columns = cursor.fetchall()
                        logger.info(f"Table structure: {columns}")
                        return []
                else:
                    logger.error("admin_trade_signals table does not exist")
                    return []
                
                # Get only required fields from admin_trade_signals (excluding CMP)
                query = """
                SELECT 
                    id,
                    symbol,
                    qty,
                    ep as entry_price,
                    created_at,
                    date,
                    pos
                FROM admin_trade_signals
                ORDER BY created_at DESC
                """

                cursor.execute(query)
                results = cursor.fetchall()

                # Find all symbol tables ending with "_5m" for price matching
                symbol_tables = [table for table in tables if table.endswith('_5m')]
                logger.info(f"Found {len(symbol_tables)} symbol tables ending with '_5m': {symbol_tables}")

                # Convert RealDictRow to regular dict and handle data types
                signals = []
                for row in results:
                    signal = dict(row)

                    # Convert dates to string if they exist
                    if signal.get('date'):
                        signal['date'] = str(
                            signal['date']) if signal['date'] else ''
                    if signal.get('created_at'):
                        signal['created_at'] = signal['created_at'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        ) if signal['created_at'] else None

                    # Ensure numeric fields are properly formatted
                    numeric_fields = ['pos', 'qty', 'entry_price']

                    for field in numeric_fields:
                        if signal.get(field) is not None:
                            try:
                                signal[field] = float(signal[field])
                            except (ValueError, TypeError):
                                signal[field] = 0.0
                    
                    # Initialize CMP to 0.0 - will be updated from symbol table
                    signal['cmp'] = 0.0

                    # Ensure string fields are properly formatted
                    if signal.get('symbol'):
                        signal['symbol'] = str(signal['symbol']).upper()
                    else:
                        signal['symbol'] = ''

                    # Try to get CMP from matching symbol table ending with "_5m"
                    symbol_name = signal.get('symbol', '').upper()
                    if symbol_name and symbol_tables:
                        # Look for matching table (case-insensitive, multiple matching strategies)
                        matching_table = None
                        
                        # Strategy 1: Exact match with symbol name
                        exact_match = f"{symbol_name}_5m".lower()
                        for table in symbol_tables:
                            if table.lower() == exact_match:
                                matching_table = table
                                break
                        
                        # Strategy 2: Table starts with symbol name
                        if not matching_table:
                            for table in symbol_tables:
                                if table.upper().startswith(symbol_name.upper()):
                                    matching_table = table
                                    break
                        
                        # Strategy 3: Symbol name is contained in table name
                        if not matching_table:
                            for table in symbol_tables:
                                if symbol_name.upper() in table.upper():
                                    matching_table = table
                                    break
                        
                        if matching_table:
                            try:
                                # First check what columns exist in the matching table
                                cursor.execute(f"""
                                    SELECT column_name 
                                    FROM information_schema.columns 
                                    WHERE table_name = '{matching_table}'
                                """)
                                columns = [col['column_name'] for col in cursor.fetchall()]
                                
                                # Build query based on available columns
                                price_columns = []
                                if 'close_price' in columns:
                                    price_columns.append('close_price')
                                if 'last_price' in columns:
                                    price_columns.append('last_price')
                                if 'close' in columns:
                                    price_columns.append('close')
                                if 'price' in columns:
                                    price_columns.append('price')
                                
                                if price_columns:
                                    # Get the latest price data from the matching table
                                    # Build ORDER BY clause based on available timestamp columns
                                    order_by_clause = "1"  # Default fallback
                                    if 'timestamp' in columns:
                                        order_by_clause = "timestamp DESC"
                                    elif 'created_at' in columns:
                                        order_by_clause = "created_at DESC"
                                    elif 'date' in columns:
                                        order_by_clause = "date DESC"
                                    elif 'id' in columns:
                                        order_by_clause = "id DESC"
                                    
                                    price_query = f"""
                                    SELECT {', '.join(price_columns)} 
                                    FROM {matching_table} 
                                    ORDER BY {order_by_clause}
                                    LIMIT 1
                                    """
                                    cursor.execute(price_query)
                                    price_data = cursor.fetchone()
                                    
                                    if price_data:
                                        # Use close_price as CMP, fallback to other price columns
                                        cmp_value = None
                                        for col in price_columns:
                                            if price_data.get(col):
                                                cmp_value = price_data.get(col)
                                                break
                                        
                                        if cmp_value:
                                            signal['cmp'] = round(float(cmp_value), 2)
                                            logger.info(f"Updated CMP for {symbol_name} from table {matching_table}: {signal['cmp']}")
                                        else:
                                            logger.warning(f"No valid price data found in {matching_table} for {symbol_name}")
                                    else:
                                        logger.warning(f"No price data found in {matching_table} for {symbol_name}")
                                else:
                                    logger.warning(f"No price columns found in {matching_table} for {symbol_name}")
                                    
                            except Exception as e:
                                logger.error(f"Error fetching price for {symbol_name} from {matching_table}: {e}")
                        else:
                            logger.info(f"No matching symbol table found for {symbol_name} among {len(symbol_tables)} tables")

                    signals.append(signal)

                logger.info(
                    f"✓ Fetched {len(signals)} admin trade signals with CMP from database"
                )
                return signals

        except Exception as e:
            logger.error(f"Error fetching admin trade signals: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []

    def get_signal_by_id(self, signal_id: int) -> Optional[Dict]:
        """Fetch specific admin trade signal by ID"""
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor)

            query = """
            SELECT * FROM admin_trade_signals 
            WHERE id = %s
            """

            cursor.execute(query, (signal_id, ))
            result = cursor.fetchone()
            cursor.close()

            if result:
                signal = dict(result)
                # Format dates and numeric fields same as above
                if signal.get('entry_date'):
                    signal['entry_date'] = signal['entry_date'].strftime(
                        '%Y-%m-%d') if signal['entry_date'] else None
                if signal.get('exit_date'):
                    signal['exit_date'] = signal['exit_date'].strftime(
                        '%Y-%m-%d') if signal['exit_date'] else None

                return signal
            return None

        except Exception as e:
            logger.error(f"Error fetching signal by ID {signal_id}: {e}")
            return None


def get_etf_signals_from_external_db() -> List[Dict]:
    """Fetch ETF signals data from external admin_trade_signals table"""
    db_service = ExternalDBService()
    try:
        signals = db_service.get_admin_trade_signals()
        return signals
    finally:
        db_service.disconnect()


def get_etf_signals_data_json(page=1, page_size=10):
    """Get ETF signals data in JSON format for API response with pagination"""
    try:
        signals = get_etf_signals_from_external_db()
        
        # If no signals found, return appropriate message
        if not signals:
            logger.info("No signals found in database - returning empty result")
            return {
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_more': False,
                'message': 'No trading signals found in admin_trade_signals table. Please check if data exists in the external database.'
            }
            
        formatted_signals = []
        count = 0

        for signal in signals:
            count += 1
            # Get only the 4 required fields from admin_trade_signals
            symbol = str(signal.get('symbol') or 'N/A').upper()
            qty = float(signal.get('qty') or 0) if signal.get('qty') is not None else 0.0
            entry_price = float(signal.get('entry_price') or 0) if signal.get('entry_price') is not None else 0.0
            
            # Get CMP from admin_trade_signals table (since symbols table doesn't exist)
            cmp = float(signal.get('cmp') or 0) if signal.get('cmp') is not None else 0.0
            
            # Calculate basic metrics
            investment = qty * entry_price if qty and entry_price else 0
            current_value = qty * cmp if qty and cmp else 0
            profit_loss = current_value - investment
            change_percent = ((cmp - entry_price) / entry_price) * 100 if entry_price > 0 else 0

            # Format the data structure
            formatted_signal = {
                'id': signal.get('id') or count,
                'trade_signal_id': signal.get('id') or count,
                'symbol': symbol,
                'etf': symbol,
                'qty': int(qty),
                'ep': round(entry_price, 2),
                'cmp': round(cmp, 2),
                'inv': round(investment, 2),
                'current_value': round(current_value, 2),
                'pl': round(profit_loss, 2),
                'chan': f"{change_percent:.2f}%",
                'change_percent': round(change_percent, 2),
                'date': signal.get('date', ''),
                'created_at': signal.get('created_at', ''),
                'pos': signal.get('pos', 1),
                # Formatted display values
                'ep_formatted': f"₹{entry_price:.2f}",
                'cmp_formatted': f"₹{cmp:.2f}",
                'inv_formatted': f"₹{investment:.2f}",
                'pl_formatted': f"₹{profit_loss:.2f}",
                'current_value_formatted': f"₹{current_value:.2f}"
            }
            formatted_signals.append(formatted_signal)

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_signals = formatted_signals[start_idx:end_idx]
        
        return {
            'data': paginated_signals,
            'recordsTotal': len(formatted_signals),
            'recordsFiltered': len(formatted_signals),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(formatted_signals) + page_size - 1) // page_size,
            'has_more': end_idx < len(formatted_signals),
            'message': f'Successfully loaded {len(paginated_signals)} signals from admin_trade_signals table'
        }

    except Exception as e:
        logger.error(f"Error getting ETF signals data: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'page': page,
            'page_size': page_size,
            'has_more': False,
            'error': str(e),
            'message': 'No trading signals found - admin_trade_signals table may be empty'
        }
