"""
External Database Service for fetching data from admin_trade_signals table
Connects to external PostgreSQL database and provides trading signals data with complete functionality

Updated with SignalsFetcher, PriceFetcher, and HistoricalFetcher classes
"""

import psycopg2
import psycopg2.extras
from psycopg2 import sql
import logging
import pandas as pd
import numbers
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Database connection handler"""
    
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
        """Establish connection to database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✓ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("✓ Disconnected from database")

    def execute_query(self, query, params=None):
        """Execute query and return results"""
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params)
            if cursor.description:
                results = cursor.fetchall()
                cursor.close()
                return results
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None


class SignalsFetcher:
    def __init__(self, db_connector):
        self.db = db_connector
        self.logger = logger
    
    def get_admin_signals(self, days_back: int = 30) -> pd.DataFrame:
        """
        Fetch admin trade signals as DataFrame
        
        Args:
            days_back: Number of days to look back for signals
            
        Returns:
            DataFrame with columns: id, symbol, qty, entry_price, created_at
        """
        try:
            query = sql.SQL("""
                SELECT 
                    id, 
                    symbol, 
                    qty, 
                    ep AS entry_price,
                    created_at
                FROM admin_trade_signals
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """)
            
            params = [datetime.now() - timedelta(days=days_back)]
            
            self.logger.debug("Executing admin signals query")
            results = self.db.execute_query(query, params)
            
            if not results:
                self.logger.warning("No admin signals found")
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            
            # Convert data types
            numeric_cols = ['qty', 'entry_price']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            # df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Clean symbol names
            df['symbol'] = df['symbol'].str.upper().str.strip()
            
            return df.dropna(subset=numeric_cols)

        except Exception as e:
            self.logger.error(f"Error fetching admin signals: {str(e)}", exc_info=True)
            return pd.DataFrame()


class PriceFetcher:
    def __init__(self, db_connector):
        self.db = db_connector
        self.logger = logger
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in symbols schema"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'symbols' 
            AND table_name = %s
        )
        """
        result = self.db.execute_query(query, (table_name,))
        return result and result[0]['exists']

    def get_cmp(self, symbol: str) -> Optional[float]:
        """
        Get current market price from _5min table
        Args:
            symbol: Stock symbol
        Returns:
            Last price or None if not available
        """
        try:
            table_name = f"{symbol.lower()}_5m"
            
            if not self.table_exists(table_name):
                self.logger.warning(f"5min table not found: {table_name}")
                return None
            
            query = sql.SQL("""
                SELECT close 
                FROM symbols.{} 
                ORDER BY datetime DESC 
                LIMIT 1
            """).format(sql.Identifier(table_name))

            result = self.db.execute_query(query)
            return float(result[0]['close']) if result else None

        except Exception as e:
            self.logger.error(f"Error fetching CMP: {str(e)}", exc_info=True)
            return None


class HistoricalFetcher:
    def __init__(self, db_connector):
        self.db = db_connector

    def table_exists(self, table_name: str) -> bool:
        query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'symbols' 
            AND table_name = %s
        )
        """
        result = self.db.execute_query(query, (table_name,))
        return result and result[0]['exists']

    def get_offset_price(self, symbol: str, offset: int) -> Optional[float]:
        """
        Return close price for N trading days ago (offset=7 or 30).
        If not enough data, return None.
        """
        try:
            table_name = f"{symbol.lower()}_daily"
            if not self.table_exists(table_name):
                logger.warning(f"Table not found: symbols.{table_name}")
                return None

            # Count rows
            count_query = sql.SQL("SELECT COUNT(*) as cnt FROM symbols.{}").format(sql.Identifier(table_name))
            count_result = self.db.execute_query(count_query)
            row_count = count_result[0]['cnt'] if count_result else 0

            if row_count <= offset:
                return None  # Not enough rows

            # Get Nth previous close: 0 = latest, 1 = 1 trading day ago, ...
            price_query = sql.SQL("""
                SELECT close FROM symbols.{}
                ORDER BY datetime DESC
                OFFSET %s LIMIT 1
            """).format(sql.Identifier(table_name))
            result = self.db.execute_query(price_query, (offset,))
            return float(result[0]['close']) if result else None
        except Exception as e:
            logger.error(f"Error fetching offset={offset} price: {e}", exc_info=True)
            return None

    def get_latest_close(self, symbol: str) -> Optional[float]:
        """
        Return close price for latest available trading day.
        """
        try:
            table_name = f"{symbol.lower()}_daily"
            if not self.table_exists(table_name):
                logger.warning(f"Table not found: symbols.{table_name}")
                return None
            price_query = sql.SQL("""
                SELECT close FROM symbols.{}
                ORDER BY datetime DESC
                LIMIT 1
            """).format(sql.Identifier(table_name))
            result = self.db.execute_query(price_query)
            return float(result[0]['close']) if result else None
        except Exception as e:
            logger.error(f"Error fetching latest close price: {e}", exc_info=True)
            return None


def try_percent(cmp_val, hist_val):
    """
    Calculate percent change if both are numbers, else '--'.
    """
    try:
        if (
            cmp_val is not None and hist_val is not None and
            isinstance(cmp_val, (int, float)) and isinstance(hist_val, (int, float)) and
            hist_val != 0 and not pd.isna(cmp_val) and not pd.isna(hist_val)
        ):
            pct_change = (float(cmp_val) - float(hist_val)) / float(hist_val) * 100
            return f"{pct_change:.2f}%"
        else:
            return '--'
    except Exception:
        return '--'


def create_db_connection():
    """Create and return database connection"""
    db_connector = DatabaseConnector()
    if db_connector.connect():
        return db_connector
    return None


def get_all_trade_metrics():
    """
    Fetches all signals from DB and enriches with price, target, and derived fields.
    Returns list of dicts for DataFrame/display.
    """
    db_connector = None
    formatted_signals = []

    try:
        # 1. Connect to database
        db_connector = create_db_connection()
        if not db_connector:
            print("Database connection failed!")
            return []

        # 2. Initialize helper/fetcher objects
        price_fetcher = PriceFetcher(db_connector)
        signals_fetcher = SignalsFetcher(db_connector)
        hist_fetcher = HistoricalFetcher(db_connector)

        # 3. Fetch all trading signals as DataFrame
        df_signals = signals_fetcher.get_admin_signals()
        if df_signals.empty:
            print("No trading signals in database!")
            return []

        # 4. For each signal, enrich and calculate all desired metrics
        for count, signal in enumerate(df_signals.to_dict(orient='records'), start=1):
            # --- Extract basic trading info ---
            symbol = str(signal.get('symbol') or 'N/A').upper()
            id_ = signal.get('id') or count
            qty = float(signal.get('qty') or 0)
            entry_price = float(signal.get('entry_price') or 0)

            # --- Format the date as dd-mm-yy HH:MM ---
            raw_date = signal.get('date', '') or signal.get('created_at', '') or ''
            if raw_date:
                try:
                    dt_obj = pd.to_datetime(raw_date)
                    date_fmt = dt_obj.strftime("%d-%m-%y %H:%M")
                except Exception:
                    date_fmt = raw_date
            else:
                date_fmt = ''

            # --- Fetch prices (CMP, 7D, 30D) ---
            cmp_val = price_fetcher.get_cmp(symbol)
            if cmp_val not in (None, "--"):
                try:
                    cmp_numeric = float(cmp_val)
                    cmp_display = cmp_numeric
                    cmp_is_num = True
                except Exception:
                    cmp_numeric = 0.0
                    cmp_display = "--"
                    cmp_is_num = False
            else:
                cmp_numeric = 0.0
                cmp_display = "--"
                cmp_is_num = False

            d7_val = hist_fetcher.get_offset_price(symbol, 7)
            d30_val = hist_fetcher.get_offset_price(symbol, 30)
            p7 = try_percent(cmp_numeric, d7_val)
            p30 = try_percent(cmp_numeric, d30_val)

            # --- Investment/Profit/Loss calculations ---
            investment = qty * entry_price
            current_value = qty * cmp_numeric if cmp_is_num else 0
            profit_loss = current_value - investment if cmp_is_num else 0
            change_percent = ((cmp_numeric - entry_price) / entry_price) * 100 if cmp_is_num and entry_price > 0 else 0

            # --- Get custom/calculated fields with fallback ---
            iv_value = signal.get('iv', investment)
            ip_value = signal.get('ip', entry_price)
            nt_value = signal.get('nt', current_value if cmp_is_num else "--")
            # Ensure robust numeric fallback
            if not isinstance(iv_value, (int, float)) or iv_value <= 0:
                iv_value = investment
            if not isinstance(ip_value, (int, float)) or ip_value <= 0:
                ip_value = entry_price
            if nt_value != "--" and (not isinstance(nt_value, (int, float)) or nt_value <= 0):
                nt_value = current_value if cmp_is_num else "--"

            # --- Target Price, TPR, TVA calculation (business logic) ---
            if entry_price > 0:
                if cmp_numeric > 0 and cmp_is_num:
                    current_gain_percent = ((cmp_numeric - entry_price) / entry_price) * 100
                    if current_gain_percent > 10:
                        target_price = entry_price * 1.25       # 25% from entry price
                    elif current_gain_percent > 5:
                        target_price = entry_price * 1.20
                    elif current_gain_percent > 0:
                        target_price = entry_price * 1.15
                    elif current_gain_percent > -5:
                        target_price = entry_price * 1.12
                    else:
                        target_price = entry_price * 1.10
                else:
                    target_price = entry_price * 1.15          # Default 15% target
                tpr_percent = ((target_price - entry_price) / entry_price) * 100
                tp_value = round(target_price, 2)
                tpr_value = f"{tpr_percent:.2f}%"
                tva_value = round(target_price * qty, 2)
            else:
                tp_value = "--"
                tpr_value = "--"
                tva_value = "--"

            # --- Additional custom fields with default fallback ---
            cpl_value = signal.get('cpl', "--")
            ed_value = signal.get('ed', "--")
            exp_value = signal.get('exp', "--")
            pr_value = signal.get('pr', "--")
            pp_value = signal.get('pp', "--")

            # --- Compose results dictionary for this trade signal ---
            row = {
                'ID': id_,
                'Symbol': symbol,
                '7D': d7_val if d7_val not in (None, "--") else "--",
                '7D%': p7,
                '30D': d30_val if d30_val not in (None, "--") else "--",
                '30D%': p30,
                'DATE': date_fmt,  # <-- Use formatted date here
                'QTY': int(qty),
                'EP': round(entry_price, 2),
                'CMP': cmp_display if cmp_is_num else "--",
                '%CHAN': f"{change_percent:.2f}%" if cmp_is_num else "--",
                'INV': round(investment, 2),
                'TP': tp_value,
                'TPR': tpr_value,
                'TVA': tva_value,
                'CPL': round(profit_loss, 2) if cmp_is_num else "--",
                'ED': ed_value,
                'EXP': exp_value,
                'PR': pr_value,
                'PP': pp_value,
                'IV': round(float(iv_value), 2),
                'IP': round(float(ip_value), 2)
            }
            formatted_signals.append(row)

        # 5. Return full list of dictionaries (for a DataFrame or other output)
        return formatted_signals

    except Exception as e:
        print(f"Trade calculation failed: {e}")
        return []
    finally:
        if db_connector:
            db_connector.disconnect()


# Legacy ExternalDBService class for backward compatibility
class ExternalDBService:
    """Service for connecting to external PostgreSQL database - Legacy class for backward compatibility"""

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
        """Legacy method - use get_all_trade_metrics() for full functionality"""
        # Convert new format to legacy format for backward compatibility
        signals = get_all_trade_metrics()
        legacy_signals = []
        
        for signal in signals:
            legacy_signal = {
                'id': signal.get('ID'),
                'symbol': signal.get('Symbol'),
                'qty': signal.get('QTY'),
                'entry_price': signal.get('EP'),
                'cmp': signal.get('CMP'),
                'created_at': signal.get('DATE'),
                'pos': 1,  # Default position
                'date': signal.get('DATE')
            }
            legacy_signals.append(legacy_signal)
        
        return legacy_signals

    def get_signal_by_id(self, signal_id: int) -> Optional[Dict]:
        """Get a single signal by ID"""
        signals = get_all_trade_metrics()
        for signal in signals:
            if signal.get('ID') == signal_id:
                return {
                    'id': signal.get('ID'),
                    'symbol': signal.get('Symbol'),
                    'qty': signal.get('QTY'),
                    'entry_price': signal.get('EP'),
                    'cmp': signal.get('CMP'),
                    'created_at': signal.get('DATE'),
                    'pos': 1,
                    'date': signal.get('DATE')
                }
        return None


# Legacy functions for backward compatibility
def get_etf_signals_from_external_db() -> List[Dict]:
    """Legacy function - redirects to new implementation"""
    return get_all_trade_metrics()


def get_etf_signals_data_json():
    """Get ETF signals data without pagination for /trading-signals page"""
    try:
        logger.info("Fetching complete ETF signals data from external database")
        
        # Get all signals using new implementation
        signals = get_all_trade_metrics()
        
        if not signals:
            logger.warning("No trading signals found in database")
            return {
                'data': [],
                'total': 0,
                'message': 'No trading signals available'
            }
        
        logger.info(f"✓ Fetched {len(signals)} trading signals successfully")
        
        return {
            'data': signals,
            'total': len(signals),
            'message': f'Successfully loaded {len(signals)} trading signals'
        }
        
    except Exception as e:
        logger.error(f"Error in get_etf_signals_data_json: {str(e)}", exc_info=True)
        return {
            'data': [],
            'total': 0,
            'error': str(e),
            'message': 'Failed to fetch trading signals'
        }


def get_basic_trade_signals_data_json():
    """Get basic trade signals data for API endpoints"""
    try:
        logger.info("Fetching basic trade signals data")
        
        # Use the new comprehensive function
        signals = get_all_trade_metrics()
        
        if not signals:
            logger.warning("No basic trade signals found")
            return {
                'data': [],
                'total': 0,
                'message': 'No basic trade signals available'
            }
        
        # Format for basic display (simplified version)
        basic_signals = []
        for signal in signals:
            basic_signal = {
                'id': signal.get('ID'),
                'symbol': signal.get('Symbol'),
                'date': signal.get('DATE'),
                'qty': signal.get('QTY'),
                'entry_price': signal.get('EP'),
                'cmp': signal.get('CMP'),
                'change_percent': signal.get('%CHAN'),
                'investment': signal.get('INV'),
                'current_value': signal.get('CPL'),
                'target_price': signal.get('TP'),
                'target_percent': signal.get('TPR')
            }
            basic_signals.append(basic_signal)
        
        logger.info(f"✓ Formatted {len(basic_signals)} basic trade signals")
        
        return {
            'data': basic_signals,
            'total': len(basic_signals),
            'message': f'Successfully loaded {len(basic_signals)} basic trade signals'
        }
        
    except Exception as e:
        logger.error(f"Error in get_basic_trade_signals_data_json: {str(e)}", exc_info=True)
        return {
            'data': [],
            'total': 0,
            'error': str(e),
            'message': 'Failed to fetch basic trade signals'
        }