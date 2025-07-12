import time
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing optional dependencies with error handling
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning(
        "psycopg2 not available. Install with: pip install psycopg2-binary")
    PSYCOPG2_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    logger.warning("pandas not available. Install with: pip install pandas")
    PANDAS_AVAILABLE = False


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []

    if not PSYCOPG2_AVAILABLE:
        missing_deps.append("psycopg2-binary")
    if not PANDAS_AVAILABLE:
        missing_deps.append("pandas")

    if missing_deps:
        raise ImportError(
            f"Missing dependencies: {', '.join(missing_deps)}. Install with: pip install {' '.join(missing_deps)}"
        )

    return True


# PostgreSQL DB config - Only use if credentials are provided
def get_db_config():
    """Get database configuration only if credentials are available"""
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    database_url = os.getenv('DATABASE_URL')
    
    # Check if we have either individual credentials or full DATABASE_URL
    if database_url:
        # Parse DATABASE_URL if provided
        return {'database_url': database_url}
    elif all([db_host, db_name, db_user, db_password]):
        # Use individual credentials
        return {
            'host': db_host,
            'database': db_name,
            'user': db_user,
            'password': db_password,
            'port': int(os.getenv('DB_PORT', 5432)),
            'connect_timeout': 5,
            'application_name': 'kotak_trading_app'
        }
    else:
        # No credentials available
        return None


@contextmanager
def get_db_connection():
    """Context manager for database connections with timeout handling"""
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 is required but not available")

    # Check if database credentials are available
    db_config = get_db_config()
    if not db_config:
        raise ConnectionError("Database credentials not configured. Please provide DATABASE_URL or individual DB credentials.")

    conn = None
    try:
        # Use very short timeout to prevent worker timeouts
        if 'database_url' in db_config:
            conn = psycopg2.connect(db_config['database_url'], connect_timeout=3)
        else:
            config_with_timeout = db_config.copy()
            config_with_timeout['connect_timeout'] = 3
            conn = psycopg2.connect(**config_with_timeout)
        
        conn.autocommit = True
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise ConnectionError(f"Cannot connect to trading database: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def test_database_connection():
    """Test database connection with quick timeout"""
    try:
        check_dependencies()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            logger.info("✅ External database connection successful")
            return result is not None
    except (ConnectionError, Exception) as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


def get_all_symbol_tables():
    """Get all table names from symbols schema"""
    try:
        check_dependencies()
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all tables from symbols schema
            cursor.execute('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'symbols' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            ''')

            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            logger.info(f"Found {len(tables)} tables in symbols schema")
            return tables

    except Exception as e:
        logger.error(f"Error getting symbol tables: {e}")
        return []


def get_symbol_data_fast(table_name):
    """Get the last row data from a symbol table quickly with minimal processing"""
    try:
        check_dependencies()
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Validate table name
            if not table_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid table name: {table_name}")

            # Quick check if table has data
            cursor.execute(
                f'SELECT COUNT(*) FROM symbols."{table_name}" LIMIT 1')
            count = cursor.fetchone()[0]
            if count == 0:
                return None

            # Get only the latest row quickly
            cursor.execute(f"""
                SELECT datetime, open, high, low, close, volume 
                FROM symbols."{table_name}" 
                ORDER BY datetime DESC 
                LIMIT 8
            """)

            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                return None

            # Get the latest (current) data
            latest_row = rows[0]
            current_close = float(latest_row[4])

            # Calculate d7 and d30 with available data
            d7_price = float(rows[min(
                7,
                len(rows) - 1)][4]) if len(rows) > 7 else current_close
            d30_price = current_close  # Simplified for speed

            # Create signal data structure
            signal_data = {
                'etf': table_name,
                'datetime': latest_row[0],
                'open': float(latest_row[1]),
                'high': float(latest_row[2]),
                'low': float(latest_row[3]),
                'close': current_close,
                'volume': float(latest_row[5]),
                'cmp': current_close,
                'd7': d7_price,
                'd30': d30_price,
                'available_rows': len(rows)
            }

            return signal_data

    except Exception as e:
        logger.error(f"Error getting fast data from {table_name}: {e}")
        return None


def get_symbol_data(table_name):
    """Get the last row data from a symbol table and calculate required fields"""
    try:
        check_dependencies()
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Use parameterized query to prevent SQL injection
            # Note: table names can't be parameterized, so we validate it first
            if not table_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid table name: {table_name}")

            # First check if table exists and has data
            cursor.execute(f"""
                SELECT COUNT(*) FROM symbols."{table_name}"
            """)

            count = cursor.fetchone()[0]
            if count == 0:
                logger.warning(f"No data found in table {table_name}")
                return None

            # Get the latest 31 rows (for 30-day calculation) ordered by datetime
            cursor.execute(f"""
                SELECT datetime, open, high, low, close, volume 
                FROM symbols."{table_name}" 
                ORDER BY datetime DESC 
                LIMIT 31
            """)

            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                logger.warning(f"No data found in table {table_name}")
                return None

            # Convert to DataFrame for easier calculation
            df = pd.DataFrame(
                rows,
                columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df = df.sort_values(
                'datetime')  # Sort ascending for proper calculation

            # Get the latest (current) data
            latest_row = df.iloc[-1]
            current_close = float(latest_row['close'])

            # Calculate d7 (7 days ago price) - get 7th row from end if available
            d7_price = float(
                df.iloc[-8]['close']) if len(df) >= 8 else current_close

            # Calculate d30 (30 days ago price) - get 30th row from end if available
            d30_price = float(
                df.iloc[-31]['close']) if len(df) >= 31 else current_close

            # Create signal data structure
            signal_data = {
                'etf': table_name,
                'datetime': latest_row['datetime'],
                'open': float(latest_row['open']),
                'high': float(latest_row['high']),
                'low': float(latest_row['low']),
                'close': current_close,
                'volume': float(latest_row['volume']),
                'cmp': current_close,  # Current Market Price = close price
                'd7': d7_price,
                'd30': d30_price,
                'available_rows': len(df)
            }

            logger.info(
                f"✅ Processed {table_name}: CMP=₹{current_close:.2f}, D7=₹{d7_price:.2f}, D30=₹{d30_price:.2f}"
            )
            return signal_data

    except Exception as e:
        logger.error(f"Error getting data from {table_name}: {e}")
        return None


def get_etf_signals_from_symbols_schema():
    """Get ETF signals from all tables in symbols schema with optimized processing"""
    try:
        check_dependencies()

        # Get all symbol tables
        tables = get_all_symbol_tables()
        if not tables:
            logger.warning("No tables found in symbols schema")
            return []

        signals = []
        count = 0
        # Filter to only _5m tables
        five_min_tables = [table for table in tables if table.endswith('_5m')]

        # Process all _5m tables as requested
        for table_name in five_min_tables:
            try:
                count += 1
                logger.info(
                    f"Processing table {count}/{len(five_min_tables)}: {table_name}"
                )

                # Get symbol data with timeout protection
                symbol_data = get_symbol_data_fast(table_name)
                if symbol_data:
                    # Create signal record with required fields
                    signal = {
                        'id':
                        count,
                        'etf':
                        table_name,
                        'date':
                        symbol_data['datetime'].strftime('%Y-%m-%d')
                        if symbol_data['datetime'] else '',
                        'pos':
                        1,  # Default position (1 for long)
                        'qty':
                        1,  # Default quantity
                        'ep':
                        symbol_data['close'],  # Entry price = current close
                        'cmp':
                        symbol_data['cmp'],
                        'ed':
                        '',  # Exit date (empty)
                        'exp':
                        '',  # Exit price (empty)
                        'iv':
                        symbol_data['close'],  # Investment value
                        'ip':
                        0.0,  # Investment percentage
                        'd7':
                        symbol_data['d7'],
                        'd30':
                        symbol_data['d30'],
                        'created_at':
                        datetime.now(),
                        # Additional OHLCV data
                        'open':
                        symbol_data['open'],
                        'high':
                        symbol_data['high'],
                        'low':
                        symbol_data['low'],
                        'volume':
                        symbol_data['volume'],
                        'available_rows':
                        symbol_data['available_rows']
                    }
                    signals.append(signal)

            except Exception as e:
                logger.error(f"Error processing table {table_name}: {e}")
                continue

        logger.info(
            f"✅ Successfully processed {len(signals)} symbols from symbols schema"
        )
        return signals

    except Exception as e:
        logger.error(f"Error getting signals from symbols schema: {e}")
        return []


def get_etf_signals_data_json():
    """Get ETF signals data in JSON format from symbols schema - Main function for export"""
    try:
        # Check dependencies first
        check_dependencies()

        # Test connection first with quick timeout
        if not test_database_connection():
            logger.error(
                "External database connection failed - returning empty data")
            return {
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'message':
                'External database connection failed. Please check database credentials.',
                'status': 'error'
            }

        # Get signals from symbols schema
        signals = get_etf_signals_from_symbols_schema()

        if not signals:
            logger.warning("No signals found in symbols schema")
            return {
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'message': 'No signals found in symbols schema',
                'status': 'warning'
            }

        formatted_signals = []

        # Track symbol counts and quantities for calculations
        symbol_counts = {}
        symbol_quantities = {}

        for signal in signals:
            symbol = signal['etf']
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            symbol_quantities[symbol] = symbol_quantities.get(
                symbol, 0) + signal['qty']

        # Process each signal
        for signal in signals:
            try:
                symbol = signal['etf']
                pos = signal['pos']
                qty = signal['qty']
                ep = signal['ep']
                cmp = signal['cmp']
                d7_price = signal['d7']
                d30_price = signal['d30']

                # Calculate investment amount
                inv = qty * ep

                # Calculate current value and P&L
                current_value = qty * cmp
                pl = current_value - inv if pos == 1 else inv - current_value

                # Calculate percentage changes with zero division protection
                chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
                ch7_percent = (
                    (cmp - d7_price) / d7_price) * 100 if d7_price > 0 else 0
                ch30_percent = ((cmp - d30_price) /
                                d30_price) * 100 if d30_price > 0 else 0

                # Calculate price changes
                chan_value = cmp - ep
                ch7_value = cmp - d7_price
                ch30_value = cmp - d30_price

                # Calculate target price (assume 3% target)
                target_percent = 3.0
                tp = ep * (1 + target_percent / 100) if pos == 1 else ep * (
                    1 - target_percent / 100)

                # Calculate target value and profit
                tva = qty * tp
                tPr = tva - inv if pos == 1 else inv - tva

                # Get trade count for symbol
                qt = symbol_counts.get(symbol, 1)

                # Investment values
                iv = inv
                ip = chan_percent
                nt = cmp * symbol_quantities.get(symbol, qty)

                formatted_signal = {
                    'trade_signal_id': signal['id'],
                    'id': signal['id'],
                    'etf': symbol,
                    'symbol': symbol,
                    'thirty': round(d30_price, 2),
                    'd30': round(d30_price, 2),
                    'dh': f"{ch30_percent:.2f}%",
                    'ch30': round(ch30_value, 2),
                    'seven': round(d7_price, 2),
                    'd7': round(d7_price, 2),
                    'ch': f"{ch7_percent:.2f}%",
                    'ch7': round(ch7_value, 2),
                    'date': signal['date'],
                    'pos': pos,
                    'qty': qty,
                    'ep': round(ep, 2),
                    'cmp': round(cmp, 2),
                    'chan': round(chan_value, 2),
                    'chan_percent': f"{chan_percent:.2f}%",
                    'inv': round(inv, 2),
                    'tp': round(tp, 2),
                    'tva': round(tva, 2),
                    'tpr': round(tPr, 2),
                    'pl': round(pl, 2),
                    'ed': signal['ed'],
                    'exp': signal['exp'],
                    'pr': 0,  # No exit profit for current positions
                    'pp': "0.00%",
                    'iv': round(iv, 2),
                    'ip': round(ip, 2),
                    'nt': round(nt, 2),
                    'qt': qt,
                    'created_at': signal['created_at'],
                    # OHLCV data
                    'open': round(signal['open'], 2),
                    'high': round(signal['high'], 2),
                    'low': round(signal['low'], 2),
                    'volume': int(signal['volume']),
                    'available_rows': signal['available_rows'],
                    # Formatted display values
                    'd30_formatted': f"₹{d30_price:.2f}",
                    'd7_formatted': f"₹{d7_price:.2f}",
                    'cmp_formatted': f"₹{cmp:.2f}",
                    'inv_formatted': f"₹{inv:.2f}",
                    'pl_formatted': f"₹{pl:.2f}",
                    'tp_formatted': f"₹{tp:.2f}",
                    'tva_formatted': f"₹{tva:.2f}",
                    'tpr_formatted': f"₹{tPr:.2f}",
                    'data_source': 'symbols_schema',
                    'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }

                formatted_signals.append(formatted_signal)

            except Exception as e:
                logger.error(
                    f"Error processing signal for {signal.get('etf', 'unknown')}: {e}"
                )
                continue

        # Summary statistics
        total_signals = len(formatted_signals)
        success_message = f"✅ Successfully processed {total_signals} signals from symbols schema."

        logger.info(success_message)

        return {
            'data': formatted_signals,
            'recordsTotal': total_signals,
            'recordsFiltered': total_signals,
            'message': success_message,
            'status': 'success',
            'data_source': 'symbols_schema',
            'symbol_stats': {
                'total_unique_symbols': len(symbol_counts),
                'symbol_trade_counts': symbol_counts,
                'symbol_quantities': symbol_quantities
            }
        }

    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'error': str(e),
            'status': 'error',
            'message': f'❌ Missing dependencies: {str(e)}'
        }
    except Exception as e:
        logger.error(f"❌ Error getting ETF signals data: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'error': str(e),
            'status': 'error',
            'message': f'❌ Error loading signals: {str(e)}'
        }


def get_symbol_statistics():
    """Get statistics about symbols in the symbols schema"""
    try:
        check_dependencies()
        tables = get_all_symbol_tables()

        symbol_stats = {}
        total_processed = 0

        for table_name in tables:
            try:
                symbol_data = get_symbol_data(table_name)
                if symbol_data:
                    total_processed += 1
                    symbol_stats[table_name] = {
                        'table_name': table_name,
                        'current_price': symbol_data['cmp'],
                        'd7_price': symbol_data['d7'],
                        'd30_price': symbol_data['d30'],
                        'volume': symbol_data['volume'],
                        'available_rows': symbol_data['available_rows'],
                        'last_update': symbol_data['datetime']
                    }
            except Exception as e:
                logger.error(f"Error getting statistics for {table_name}: {e}")
                continue

        logger.info(
            f"✅ Processed {total_processed} symbols from symbols schema")
        return symbol_stats

    except Exception as e:
        logger.error(f"❌ Error getting symbol statistics: {e}")
        return {}


# ✅ PUBLIC API FUNCTIONS - These are the functions that should be imported
def get_etf_signals_data_json_export():
    """Main export function for ETF signals data"""
    return get_etf_signals_data_json()


def get_symbol_statistics_export():
    """Export function for symbol statistics"""
    return get_symbol_statistics()


def get_all_symbol_tables_export():
    """Export function for getting all symbol tables"""
    return get_all_symbol_tables()


def test_connection_export():
    """Export function for testing database connection"""
    return test_database_connection()


# ✅ MAIN EXECUTION
def main():
    """Main function for script execution"""
    print("🔄 Starting ETF Signals Processing from Symbols Schema...")

    # Check dependencies first
    try:
        check_dependencies()
    except ImportError as e:
        print(f"❌ {e}")
        return False

    # Test database connection
    print("\n1. Testing database connection...")
    if test_database_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return False

    # Get all symbol tables
    print("\n2. Getting symbol tables from symbols schema...")
    tables = get_all_symbol_tables()
    print(f"✅ Found {len(tables)} tables in symbols schema")

    if not tables:
        print("❌ No tables found in symbols schema")
        return False

    # Get symbol statistics
    print("\n3. Getting symbol statistics...")
    stats = get_symbol_statistics()
    print(f"✅ Found {len(stats)} symbols with data:")
    for i, (symbol, data) in enumerate(stats.items()):
        if i >= 10:  # Show first 10
            break
        print(
            f"  📊 {symbol}: CMP=₹{data['current_price']:.2f}, D7=₹{data['d7_price']:.2f}, D30=₹{data['d30_price']:.2f}, Rows={data['available_rows']}"
        )

    if len(stats) > 10:
        print(f"  ... and {len(stats) - 10} more symbols")

    # Get formatted signals data
    print("\n4. Fetching and processing signals data...")
    result = get_etf_signals_data_json()

    print(f"\n🎯 FINAL RESULT:")
    print(f"✅ {result['message']}")
    print(f"📊 Total signals: {result['recordsTotal']}")
    print(f"🔄 Data source: {result.get('data_source', 'symbols_schema')}")
    print(f"📋 Status: {result.get('status', 'unknown')}")

    if result.get('symbol_stats'):
        print(
            f"🏷️  Unique symbols processed: {result['symbol_stats']['total_unique_symbols']}"
        )
        symbol_counts = result['symbol_stats']['symbol_trade_counts']
        if symbol_counts:
            print(
                f"📈 Symbol trade counts: {dict(list(symbol_counts.items())[:5])}"
            )  # Show first 5

    # Show sample data
    if result['data']:
        print(f"\n📋 Sample data (first signal):")
        sample = result['data'][0]
        print(f"  Symbol: {sample['symbol']}")
        print(f"  Current Price: {sample['cmp_formatted']}")
        print(f"  D7 Price: {sample['d7_formatted']}")
        print(f"  D30 Price: {sample['d30_formatted']}")
        print(f"  Volume: {sample['volume']:,}")
        print(f"  Available Rows: {sample['available_rows']}")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

# ✅ EXPLICIT EXPORTS FOR IMPORT
__all__ = [
    'get_etf_signals_data_json', 'get_etf_signals_data_json_export',
    'get_symbol_statistics_export', 'get_all_symbol_tables_export',
    'test_connection_export', 'check_dependencies'
]
