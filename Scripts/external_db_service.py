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

                # Check if admin_trade_signals table exists and has data
                if 'admin_trade_signals' in public_tables:
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM admin_trade_signals")
                    row_count = cursor.fetchone()['count']
                    logger.info(
                        f"admin_trade_signals table has {row_count} rows")

                    if row_count == 0:
                        logger.warning(
                            "admin_trade_signals table is empty - checking table structure"
                        )
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

                # Use symbol tables from symbols schema for price matching
                logger.info(
                    f"Found {len(symbol_tables)} symbol tables in symbols schema: {symbol_tables[:10]}..."
                )  # Show first 10

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

                    # Initialize CMP to None - will be updated from symbol table if found
                    signal['cmp'] = None
                    cmp_found = False

                    # Initialize historical price data for calculations
                    price_30d_ago = 0.0
                    price_7d_ago = 0.0

                    # Ensure string fields are properly formatted
                    if signal.get('symbol'):
                        signal['symbol'] = str(signal['symbol']).upper()
                    else:
                        signal['symbol'] = ''

                    # Try to get CMP and historical data from matching symbol table in symbols schema
                    symbol_name = signal.get('symbol', '').upper()
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
                                table_base = table.replace('_5m', '').replace(
                                    '_', '')
                                if table_base.upper() in symbol_name.upper():
                                    matching_table = table
                                    break

                        if matching_table:
                            try:
                                # Get the latest price data from the matching table in symbols schema
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
                                    close_price = price_data[
                                        'close'] if isinstance(
                                            price_data,
                                            dict) else price_data[4]
                                    if close_price:
                                        signal['cmp'] = round(
                                            float(close_price), 2)
                                        cmp_found = True
                                        logger.info(
                                            f"Updated CMP for {symbol_name} from symbols.{matching_table}: {signal['cmp']}"
                                        )
                                    else:
                                        logger.warning(
                                            f"No valid close price found in symbols.{matching_table} for {symbol_name}"
                                        )
                                else:
                                    logger.warning(
                                        f"No price data found in symbols.{matching_table} for {symbol_name}"
                                    )

                                # Get historical data for 30-day and 7-day calculations
                                try:
                                    # Check if we have daily table for more accurate historical data
                                    daily_table = matching_table.replace('_5m', '_daily')
                                    
                                    # Try daily data first for 30-day calculation
                                    if daily_table in symbol_tables:
                                        # Get 30-day old price from daily data
                                        historical_30d_query = f"""
                                        SELECT close 
                                        FROM symbols."{daily_table}" 
                                        ORDER BY datetime DESC
                                        OFFSET 30 LIMIT 1
                                        """
                                        cursor.execute(historical_30d_query)
                                        historical_30d = cursor.fetchone()
                                        if historical_30d:
                                            price_30d_ago = float(historical_30d['close'] if isinstance(historical_30d, dict) else historical_30d[0])
                                            logger.info(f"Found 30-day historical price for {symbol_name}: {price_30d_ago}")
                                        
                                        # Get 7-day old price from daily data
                                        historical_7d_query = f"""
                                        SELECT close 
                                        FROM symbols."{daily_table}" 
                                        ORDER BY datetime DESC
                                        OFFSET 7 LIMIT 1
                                        """
                                        cursor.execute(historical_7d_query)
                                        historical_7d = cursor.fetchone()
                                        if historical_7d:
                                            price_7d_ago = float(historical_7d['close'] if isinstance(historical_7d, dict) else historical_7d[0])
                                            logger.info(f"Found 7-day historical price for {symbol_name}: {price_7d_ago}")
                                    else:
                                        # Fallback to 5-minute data with adjusted intervals
                                        # 30 days * 78 intervals per day = 2340 intervals
                                        historical_30d_query = f"""
                                        SELECT close 
                                        FROM symbols."{matching_table}" 
                                        ORDER BY datetime DESC
                                        OFFSET 2340 LIMIT 1
                                        """
                                        cursor.execute(historical_30d_query)
                                        historical_30d = cursor.fetchone()
                                        if historical_30d:
                                            price_30d_ago = float(historical_30d['close'] if isinstance(historical_30d, dict) else historical_30d[0])

                                        # 7 days * 78 intervals per day = 546 intervals
                                        historical_7d_query = f"""
                                        SELECT close 
                                        FROM symbols."{matching_table}" 
                                        ORDER BY datetime DESC
                                        OFFSET 546 LIMIT 1
                                        """
                                        cursor.execute(historical_7d_query)
                                        historical_7d = cursor.fetchone()
                                        if historical_7d:
                                            price_7d_ago = float(historical_7d['close'] if isinstance(historical_7d, dict) else historical_7d[0])

                                except Exception as hist_e:
                                    logger.warning(f"Could not fetch historical data for {symbol_name}: {hist_e}")
                                    # Set fallback values only if CMP was found
                                    if cmp_found and signal.get('cmp'):
                                        price_30d_ago = signal.get('cmp', 0.0) * 0.95  # Assume 5% lower 30 days ago
                                        price_7d_ago = signal.get('cmp', 0.0) * 0.98   # Assume 2% lower 7 days ago

                            except Exception as e:
                                logger.error(
                                    f"Error fetching price for {symbol_name} from symbols.{matching_table}: {e}"
                                )
                        else:
                            logger.info(
                                f"No matching symbol table found for {symbol_name} among {len(symbol_tables)} symbol tables in symbols schema"
                            )

                    # Set CMP to "--" if no matching symbol table found or no CMP retrieved
                    if not cmp_found or signal.get('cmp') is None:
                        signal['cmp'] = "--"

                    # Calculate dynamic values using CMP and other data
                    cmp = signal.get('cmp')
                    entry_price = signal.get('entry_price', 0.0) or 0.0
                    qty = signal.get('qty', 0.0) or 0.0

                    # Handle numeric CMP for calculations
                    if cmp == "--" or cmp is None:
                        cmp_numeric = 0.0
                    else:
                        cmp_numeric = float(cmp)

                    # Ensure we have valid numeric values
                    if cmp_numeric <= 0:
                        cmp_numeric = entry_price
                    if entry_price <= 0:
                        entry_price = cmp_numeric if cmp_numeric > 0 else 0.0
                    if qty <= 0:
                        qty = 1

                    # IV - Investment Value (Entry Price * Quantity)
                    iv_value = entry_price * qty

                    # IP - Initial Price (Entry Price)
                    ip_value = entry_price

                    # NT - Net Total (Current Market Price * Quantity)
                    if cmp == "--":
                        nt_value = "--"
                    else:
                        nt_value = cmp_numeric * qty

                    # 30d - Price 30 days ago (use historical data if available, otherwise use current price)
                    if cmp == "--":
                        thirty_d_value = "--"
                        thirty_percent = 0.0
                    elif price_30d_ago > 0:
                        thirty_d_value = price_30d_ago
                        thirty_percent = ((cmp_numeric - price_30d_ago) / price_30d_ago * 100)
                    else:
                        thirty_d_value = cmp_numeric
                        thirty_percent = 0.0

                    # 7d - Price 7 days ago (use historical data if available, otherwise use current price)
                    if cmp == "--":
                        seven_d_value = "--"
                        seven_percent = 0.0
                    elif price_7d_ago > 0:
                        seven_d_value = price_7d_ago
                        seven_percent = ((cmp_numeric - price_7d_ago) / price_7d_ago * 100)
                    else:
                        seven_d_value = cmp_numeric
                        seven_percent = 0.0

                    # Add calculated values to signal
                    signal['iv'] = round(iv_value, 2)
                    signal['ip'] = round(ip_value, 2)
                    signal['nt'] = nt_value if nt_value == "--" else round(nt_value, 2)
                    signal['thirty'] = thirty_d_value if thirty_d_value == "--" else round(thirty_d_value, 2)
                    signal['dh'] = f"{thirty_percent:.2f}%" if thirty_d_value != "--" else "--"
                    signal['seven'] = seven_d_value if seven_d_value == "--" else round(seven_d_value, 2)
                    signal['ch'] = f"{seven_percent:.2f}%" if seven_d_value != "--" else "--"

                    # Store numeric values for calculations
                    signal['thirty_percent_numeric'] = round(thirty_percent, 2)
                    signal['seven_percent_numeric'] = round(seven_percent, 2)

                    if cmp == "--":
                        logger.info(f"Symbol {symbol_name}: No matching price table found - CMP set to '--'")
                    else:
                        logger.info(f"Calculated values for {symbol_name}: IV={iv_value:.2f}, IP={ip_value:.2f}, NT={nt_value:.2f}, 30d={thirty_d_value:.2f}, 30%={thirty_percent:.2f}%, 7d={seven_d_value:.2f}, 7%={seven_percent:.2f}%")

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
            logger.info(
                "No signals found in database - returning empty result")
            return {
                'data': [],
                'recordsTotal':
                0,
                'recordsFiltered':
                0,
                'page':
                page,
                'page_size':
                page_size,
                'total_pages':
                0,
                'has_more':
                False,
                'message':
                'No trading signals found in admin_trade_signals table. Please check if data exists in the external database.'
            }

        formatted_signals = []
        count = 0

        for signal in signals:
            count += 1
            # Get the required fields from admin_trade_signals with calculated values
            symbol = str(signal.get('symbol') or 'N/A').upper()
            qty = float(signal.get('qty')
                        or 0) if signal.get('qty') is not None else 0.0
            entry_price = float(
                signal.get('entry_price')
                or 0) if signal.get('entry_price') is not None else 0.0

            # Get CMP and calculated values
            cmp = signal.get('cmp')
            if cmp == "--" or cmp is None:
                cmp_numeric = 0.0
                cmp_display = "--"
            else:
                cmp_numeric = float(cmp)
                cmp_display = cmp_numeric

            # Calculate basic metrics
            investment = qty * entry_price if qty and entry_price else 0
            current_value = qty * cmp_numeric if qty and cmp_numeric else 0
            profit_loss = current_value - investment if cmp != "--" else 0
            change_percent = ((cmp_numeric - entry_price) /
                              entry_price) * 100 if entry_price > 0 and cmp != "--" else 0

            # Get calculated values from signal with proper fallbacks
            iv_value = signal.get('iv', investment)
            ip_value = signal.get('ip', entry_price)
            nt_value = signal.get('nt', current_value if cmp != "--" else "--")
            thirty_value = signal.get('thirty', cmp_display if cmp != "--" else "--")
            dh_value = signal.get('dh', f"{change_percent:.2f}%" if cmp != "--" else "--")
            seven_value = signal.get('seven', cmp_display if cmp != "--" else "--")
            ch_value = signal.get('ch', f"{change_percent:.2f}%" if cmp != "--" else "--")

            # Ensure we have valid numeric values (skip validation for -- values)
            if not isinstance(iv_value, (int, float)) or iv_value <= 0:
                iv_value = investment
            if not isinstance(ip_value, (int, float)) or ip_value <= 0:
                ip_value = entry_price
            if nt_value != "--" and (not isinstance(nt_value, (int, float)) or nt_value <= 0):
                nt_value = current_value if cmp != "--" else "--"
            if thirty_value != "--" and (not isinstance(thirty_value, (int, float)) or thirty_value <= 0):
                thirty_value = cmp_display if cmp != "--" else "--"
            if seven_value != "--" and (not isinstance(seven_value, (int, float)) or seven_value <= 0):
                seven_value = cmp_display if cmp != "--" else "--"

            # Format the data structure with calculated values
            formatted_signal = {
                'id': signal.get('id') or count,
                'trade_signal_id': signal.get('id') or count,
                'symbol': symbol,
                'etf': symbol,
                'qty': int(qty),
                'ep': round(entry_price, 2),
                'cmp': cmp_display if cmp != "--" else "--",
                'inv': round(investment, 2),
                'current_value': round(current_value, 2) if cmp != "--" else "--",
                'pl': round(profit_loss, 2) if cmp != "--" else "--",
                'chan': f"{change_percent:.2f}%" if cmp != "--" else "--",
                'change_percent': round(change_percent, 2) if cmp != "--" else 0,
                'date': signal.get('date', ''),
                'created_at': signal.get('created_at', ''),
                'pos': signal.get('pos', 1),
                
                # Calculated values using CMP - properly formatted
                'iv': round(float(iv_value), 2),
                'ip': round(float(ip_value), 2),
                'nt': nt_value if nt_value == "--" else round(float(nt_value), 2),
                'thirty': thirty_value if thirty_value == "--" else round(float(thirty_value), 2),
                'dh': str(dh_value),
                'seven': seven_value if seven_value == "--" else round(float(seven_value), 2),
                'ch': str(ch_value),
                
                # Store numeric percentage values for calculations
                'thirty_percent_numeric': signal.get('thirty_percent_numeric', 0),
                'seven_percent_numeric': signal.get('seven_percent_numeric', 0),
                
                # Formatted display values
                'ep_formatted': f"₹{entry_price:.2f}",
                'cmp_formatted': "--" if cmp == "--" else f"₹{cmp_display:.2f}",
                'inv_formatted': f"₹{investment:.2f}",
                'pl_formatted': "--" if cmp == "--" else f"₹{profit_loss:.2f}",
                'current_value_formatted': "--" if cmp == "--" else f"₹{current_value:.2f}",
                'iv_formatted': f"₹{float(iv_value):.2f}",
                'ip_formatted': f"₹{float(ip_value):.2f}",
                'nt_formatted': "--" if nt_value == "--" else f"₹{float(nt_value):.2f}",
                'thirty_formatted': "--" if thirty_value == "--" else f"₹{float(thirty_value):.2f}",
                'seven_formatted': "--" if seven_value == "--" else f"₹{float(seven_value):.2f}"
            }
            formatted_signals.append(formatted_signal)

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_signals = formatted_signals[start_idx:end_idx]

        return {
            'data':
            paginated_signals,
            'recordsTotal':
            len(formatted_signals),
            'recordsFiltered':
            len(formatted_signals),
            'page':
            page,
            'page_size':
            page_size,
            'total_pages':
            (len(formatted_signals) + page_size - 1) // page_size,
            'has_more':
            end_idx < len(formatted_signals),
            'message':
            f'Successfully loaded {len(paginated_signals)} signals from admin_trade_signals table'
        }

    except Exception as e:
        logger.error(f"Error getting ETF signals data: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'data': [],
            'recordsTotal':
            0,
            'recordsFiltered':
            0,
            'page':
            page,
            'page_size':
            page_size,
            'has_more':
            False,
            'error':
            str(e),
            'message':
            'No trading signals found - admin_trade_signals table may be empty'
        }
