"""
Deals API - External Database Integration
Handles all deals-related operations with external PostgreSQL database
"""
import logging
from flask import Blueprint, request, jsonify, session
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from datetime import datetime, timedelta
import traceback
import os
import sys
import pandas as pd
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append('Scripts')
try:
    from config.database_config import DatabaseConfig, get_db_connection
    # Use centralized database configuration
    logger.info("✓ Using centralized database configuration")
    USE_CENTRALIZED_CONFIG = True
except ImportError:
    # Fallback to old DatabaseConnector if needed
    logger.warning("Centralized config not available, using fallback")
    try:
        from Scripts.db_connector import DatabaseConnector
    except ImportError:
        from db_connector import DatabaseConnector
    USE_CENTRALIZED_CONFIG = False

deals_api = Blueprint('deals_api', __name__, url_prefix='/api')


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
        result = self.db.execute_query(query, (table_name, ))
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
            if not symbol or not isinstance(symbol, str):
                return None

            table_name = f"{symbol.lower()}_5m"

            if not self.table_exists(table_name):
                self.logger.warning(f"5min table not found: {table_name}")
                return None

            query = f"""
                SELECT close 
                FROM symbols.{table_name} 
                ORDER BY datetime DESC 
                LIMIT 1
            """

            result = self.db.execute_query(query)
            if result and len(result) > 0 and 'close' in result[0]:
                return round(float(result[0]['close']), 2)
            return None

        except Exception as e:
            self.logger.error(f"Error fetching CMP: {str(e)}")
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
        result = self.db.execute_query(query, (table_name, ))
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
            count_query = f"SELECT COUNT(*) as cnt FROM symbols.{table_name}"
            count_result = self.db.execute_query(count_query)
            if count_result and len(
                    count_result) > 0 and 'cnt' in count_result[0]:
                row_count = count_result[0]['cnt']
            else:
                row_count = 0

            if row_count <= offset:
                return None  # Not enough rows

            # Get Nth previous close: 0 = latest, 1 = 1 trading day ago, ...
            price_query = f"""
                SELECT close FROM symbols.{table_name}
                ORDER BY datetime DESC
                OFFSET {offset} LIMIT 1
            """
            result = self.db.execute_query(price_query)
            if result and len(result) > 0 and 'close' in result[0]:
                return round(float(result[0]['close']), 2)
            return None
        except Exception as e:
            logger.error(f"Error fetching offset={offset} price: {e}")
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
            price_query = f"""
                SELECT close FROM symbols.{table_name}
                ORDER BY datetime DESC
                LIMIT 1
            """
            result = self.db.execute_query(price_query)
            if result and len(result) > 0 and 'close' in result[0]:
                return round(float(result[0]['close']), 2)
            return None
        except Exception as e:
            logger.error(f"Error fetching latest close price: {e}")
            return None


class SignalsFetcher:

    def __init__(self, db_connector):
        self.db = db_connector
        self.logger = logger

    def get_user_deals(self,
                       user_id: int = 1,
                       days_back: int = 30) -> pd.DataFrame:
        """
        Fetch user deals as DataFrame

        Args:
            user_id: User ID to fetch deals for
            days_back: Number of days to look back for deals

        Returns:
            DataFrame with columns: trade_signal_id, symbol, qty, entry_date, entry_price, position_type, ed
        """
        try:
            query = """
                SELECT 
                    id as trade_signal_id,
                    symbol, 
                    quantity as qty, 
                    entry_date as date,
                    entry_price as ep,
                    position_type as pos,
                    CASE 
                        WHEN status = 'CLOSED' AND ed IS NOT NULL THEN ed::text
                        ELSE '--'
                    END as ed,
                    COALESCE(status, 'ACTIVE') as status
                FROM user_deals
                WHERE user_id = %s
                ORDER BY entry_date DESC
            """

            params = [user_id]

            self.logger.debug("Executing user deals query")
            self.logger.debug(f"Query params: user_id={user_id}")
            results = self.db.execute_query(query, params)

            self.logger.debug(f"Query results: {results}")

            if not results:
                self.logger.warning("No user deals found")
                return pd.DataFrame()

            self.logger.info(f"Found {len(results)} user deals")
            df = pd.DataFrame(results)

            # Convert data types
            numeric_cols = ['qty', 'ep']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Clean symbol names
            if 'symbol' in df.columns:
                df['symbol'] = df['symbol'].str.upper().str.strip()

            return df.dropna(
                subset=[col for col in numeric_cols if col in df.columns])

        except Exception as e:
            self.logger.error(f"Error fetching user deals: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()


def try_percent(cmp_val, hist_val):
    """
    Calculate percent change if both are numbers, else '--'.
    """
    try:
        if (cmp_val is not None and hist_val is not None
                and isinstance(cmp_val, (int, float))
                and isinstance(hist_val, (int, float)) and hist_val != 0
                and not pd.isna(cmp_val) and not pd.isna(hist_val)):
            pct_change = (float(cmp_val) -
                          float(hist_val)) / float(hist_val) * 100
            return f"{pct_change:.2f}%"
        else:
            return '--'
    except Exception:
        return '--'


@deals_api.route('/test-deals', methods=['GET'])
def test_deals():
    """Test endpoint to verify blueprint registration"""
    return jsonify({
        'message': 'Deals API blueprint is working',
        'success': True
    })


def get_external_db_connection():
    """Get connection to external PostgreSQL database using centralized config"""
    try:
        from config.database_config import get_db_connection
        conn = get_db_connection()
        logger.info("✓ Connected to external PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to external database: {e}")
        return None


def check_duplicate_deal(symbol, username):
    """
    Check if a deal with the same symbol already exists for the user in their dynamic table
    Returns True if duplicate exists, False otherwise
    """
    try:
        # Import dynamic deals service
        import sys
        sys.path.append('scripts')
        from scripts.dynamic_user_deals import DynamicUserDealsService

        dynamic_deals_service = DynamicUserDealsService()

        # Check if user table exists
        if not dynamic_deals_service.table_exists(username):
            return False  # No table means no duplicates

        # Get user deals and check for duplicates
        existing_deals = dynamic_deals_service.get_user_deals(username)
        for deal in existing_deals:
            if (deal.get('symbol', '').upper() == symbol.upper()
                    and deal.get('status') == 'ACTIVE'):
                return True

        return False

    except Exception as e:
        logger.error(f"Error checking duplicate deal: {e}")
        return False


def get_user_deals_from_db():
    """
    Get user deals from external database public.user_deals table
    Returns all authentic deals with proper structure for calculations
    """
    try:
        conn = get_external_db_connection()
        if not conn:
            logger.error("Failed to connect to external database")
            return []

        with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Query to get all user deals from external database
            query = """
            SELECT 
                id,
                user_id,
                symbol,
                trading_symbol,
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
                updated_at
            FROM public.user_deals 
            WHERE status = 'ACTIVE'
            ORDER BY created_at DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            deals = []
            for row in rows:
                deal = dict(row)
                # Ensure numeric fields are properly formatted
                deal['entry_price'] = float(
                    deal['entry_price']) if deal['entry_price'] else 0.0
                deal['current_price'] = float(
                    deal['current_price']) if deal['current_price'] else 0.0
                deal['invested_amount'] = float(
                    deal['invested_amount']
                ) if deal['invested_amount'] else 0.0
                deal['current_value'] = float(
                    deal['current_value']) if deal['current_value'] else 0.0
                deal['pnl_amount'] = float(
                    deal['pnl_amount']) if deal['pnl_amount'] else 0.0
                deal['pnl_percent'] = float(
                    deal['pnl_percent']) if deal['pnl_percent'] else 0.0
                deals.append(deal)

        conn.close()
        logger.info(
            f"✓ Fetched {len(deals)} user deals from external database")
        return deals

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        traceback.print_exc()
        return []


def get_all_deals_data_metrics():
    """
    Fetches all user deals from DB and enriches with price, target, and derived fields.
    Returns list of dicts for DataFrame/display.
    """
    db_connector = None
    formatted_deals = []

    try:
        # 1. Connect to external database using centralized config
        if USE_CENTRALIZED_CONFIG:
            from config.database_config import get_database_url
            external_db_url = get_database_url()
            db_connector = DatabaseConnector(external_db_url)
        else:
            # Use fallback database connector
            db_connector = DatabaseConnector()
        if not db_connector:
            logger.error("External database connection failed!")
            return []

        # 2. Initialize helper/fetcher objects
        price_fetcher = PriceFetcher(db_connector)
        signals_fetcher = SignalsFetcher(db_connector)
        hist_fetcher = HistoricalFetcher(db_connector)

        # 3. Get user_id from session
        user_id = session.get('user_id')
        if not user_id or not isinstance(user_id, int):
            user_id = 1

        # 4. Fetch all user deals as DataFrame
        df_deals = signals_fetcher.get_user_deals(user_id)
        if df_deals.empty:
            logger.info("No user deals in database!")
            return []

        # 5. Count symbol occurrences for QT calculation
        symbol_counts = {}
        all_deals_data = df_deals.to_dict(orient='records')
        for deal in all_deals_data:
            symbol = str(deal.get('symbol') or 'N/A').upper()
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        # 6. For each deal, enrich and calculate all desired metrics
        for count, deal in enumerate(all_deals_data, start=1):
            # --- Extract basic trading info ---
            symbol = str(deal.get('symbol') or 'N/A').upper()
            trade_signal_id = deal.get('trade_signal_id') or count
            qty = float(deal.get('qty') or 0)
            entry_price = float(deal.get('ep') or 0)

            # --- QT = Symbol repeat count ---
            qt_value = symbol_counts.get(symbol, 1)

            # --- Format the date as dd-mm-yy HH:MM ---
            raw_date = deal.get('date', '') or ''
            if raw_date:
                try:
                    dt_obj = pd.to_datetime(raw_date)
                    date_fmt = dt_obj.strftime("%d-%m-%y %H:%M")
                except Exception:
                    date_fmt = str(raw_date)
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

            d7_val = hist_fetcher.get_offset_price(symbol, 5)
            d30_val = hist_fetcher.get_offset_price(symbol, 20)
            p7 = try_percent(cmp_numeric, d7_val)
            p30 = try_percent(cmp_numeric, d30_val)

            # --- Investment/Profit/Loss calculations ---
            investment = qty * entry_price
            current_value = qty * cmp_numeric if cmp_is_num else 0
            profit_loss = current_value - investment if cmp_is_num else 0
            change_percent = (
                (cmp_numeric - entry_price) /
                entry_price) * 100 if cmp_is_num and entry_price > 0 else 0

            # --- Target Price, TPR, TVA calculation (business logic) ---
            if entry_price > 0:
                if cmp_numeric > 0 and cmp_is_num:
                    current_gain_percent = (
                        (cmp_numeric - entry_price) / entry_price) * 100
                    if current_gain_percent > 10:
                        target_price = entry_price * 1.25  # 25% from entry price
                    elif current_gain_percent > 5:
                        target_price = entry_price * 1.20
                    elif current_gain_percent > 0:
                        target_price = entry_price * 1.15
                    elif current_gain_percent > -5:
                        target_price = entry_price * 1.12
                    else:
                        target_price = entry_price * 1.10
                else:
                    target_price = entry_price * 1.15  # Default 15% target
                tpr_percent = (
                    (target_price - entry_price) / entry_price) * 100
                tp_value = round(target_price, 2)
                tpr_value = f"{tpr_percent:.2f}%"
                tva_value = round(target_price * qty, 2)
            else:
                tp_value = "--"
                tpr_value = "--"
                tva_value = "--"

            # --- Set pos to 0 if deal is closed, otherwise use original value ---
            deal_status = str(deal.get('status', 'ACTIVE')).upper()
            pos_value = '0' if deal_status == 'CLOSED' else deal.get(
                'pos', '1')

            # --- Format deal with all required fields ---
            formatted_deal = {
                'trade_signal_id': trade_signal_id,
                'symbol': symbol,
                'seven': d7_val if d7_val else '--',
                'seven_percent': p7,
                'thirty': d30_val if d30_val else '--',
                'thirty_percent': p30,
                'date': date_fmt,
                'qty': qty,
                'ep': entry_price,
                'cmp': cmp_display,
                'pos': pos_value,
                'chan_percent': round(change_percent, 2),
                'inv': investment,
                'tp': tp_value,  # Target price with business logic
                'tpr': tpr_value,  # Target profit return percentage
                'tva': tva_value,  # Target value amount
                'pl': round(profit_loss, 2),
                'qt': qt_value,  # Symbol repeat count
                'ed': deal.get('ed', '--'),  # Exit date
                'exp': '--',  # Expiry
                'pr': '--',  # Price range
                'pp': '--',  # Performance points
                'iv': investment,  # Investment value
                'ip': entry_price,  # Entry price
                'status': deal_status,  # Use actual status from database
                'deal_type': 'MANUAL',
                'notes': '',
                'tags': '',
                'created_at': '',
                'updated_at': ''
            }
            formatted_deals.append(formatted_deal)

        # Close database connection
        if db_connector:
            db_connector.close()

        return formatted_deals

    except Exception as e:
        logger.error(f"Error in get_all_deals_data_metrics: {e}")
        if db_connector:
            db_connector.close()
        return []


#  ************* USER DEALS API **************
@deals_api.route('/user-deals-data')
def get_user_deals_data():
    """API endpoint to get user deals data from logged-in user's dynamic table"""
    try:
        # Get username from session
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'message': 'User not logged in',
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            }), 401

        # Import dynamic deals service
        import sys
        sys.path.append('scripts')
        from scripts.dynamic_user_deals import DynamicUserDealsService

        dynamic_deals_service = DynamicUserDealsService()

        # Check if user table exists
        if not dynamic_deals_service.table_exists(username):
            return jsonify({
                'success': True,
                'message': f'No deals table found for user {username}',
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            })

        # Get deals from user's dynamic table
        user_deals = dynamic_deals_service.get_user_deals(username)

        if not user_deals:
            return jsonify({
                'success': True,
                'message': f'No deals found for user {username}',
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            })

        # Calculate symbol counts for QT (repeated symbol count)
        symbol_counts = {}
        for deal in user_deals:
            symbol = str(deal.get('symbol', '')).upper()
            if symbol:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        # Format deals for frontend
        formatted_deals = []
        total_invested = 0
        total_current_value = 0
        total_pnl = 0

        for deal in user_deals:
            # Get CMP for the symbol using PriceFetcher
            db_connector = None
            try:
                from config.database_config import get_database_url, DatabaseConnector
                external_db_url = get_database_url()
                db_connector = DatabaseConnector(external_db_url)

                if db_connector:
                    db_connector.close()
            except Exception as e:
                logger.warning(
                    f"Could not fetch CMP for {deal.get('symbol', '')}: {e}")
                # cmp = deal.get('ep', 0)  # Fallback to entry price

            # --- Extract basic trading info ---

            symbol_counts = {}

            # 2. Initialize helper/fetcher objects
            price_fetcher = PriceFetcher(db_connector)
            signals_fetcher = SignalsFetcher(db_connector)
            hist_fetcher = HistoricalFetcher(db_connector)

            symbol = str(deal.get('symbol') or 'N/A').upper()
            trade_signal_id = deal.get('trade_signal_id')
            qty = float(deal.get('qty') or 0)
            entry_price = float(deal.get('ep') or 0)

            # --- QT = Symbol repeat count ---
            qt_value = symbol_counts.get(symbol, 1)

            # --- Format the date as dd-mm-yy HH:MM ---
            raw_date = deal.get('date', '') or ''
            if raw_date:
                try:
                    dt_obj = pd.to_datetime(raw_date)
                    date_fmt = dt_obj.strftime("%d-%m-%y %H:%M")
                except Exception:
                    date_fmt = str(raw_date)
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

            d7_val = hist_fetcher.get_offset_price(symbol, 5)
            d30_val = hist_fetcher.get_offset_price(symbol, 20)
            p7 = try_percent(cmp_numeric, d7_val)
            p30 = try_percent(cmp_numeric, d30_val)

            # --- Investment/Profit/Loss calculations ---
            investment = qty * entry_price
            current_value = qty * cmp_numeric if cmp_is_num else 0
            profit_loss = current_value - investment if cmp_is_num else 0
            change_percent = (
                (cmp_numeric - entry_price) /
                entry_price) * 100 if cmp_is_num and entry_price > 0 else 0

            # --- Target Price, TPR, TVA calculation (business logic) ---
            if entry_price > 0:
                if cmp_numeric > 0 and cmp_is_num:
                    current_gain_percent = (
                        (cmp_numeric - entry_price) / entry_price) * 100
                    if current_gain_percent > 10:
                        target_price = entry_price * 1.25  # 25% from entry price
                    elif current_gain_percent > 5:
                        target_price = entry_price * 1.20
                    elif current_gain_percent > 0:
                        target_price = entry_price * 1.15
                    elif current_gain_percent > -5:
                        target_price = entry_price * 1.12
                    else:
                        target_price = entry_price * 1.10
                else:
                    target_price = entry_price * 1.15  # Default 15% target
                tpr_percent = (
                    (target_price - entry_price) / entry_price) * 100
                tp_value = round(target_price, 2)
                tpr_value = f"{tpr_percent:.2f}%"
                tva_value = round(target_price * qty, 2)
            else:
                tp_value = "--"
                tpr_value = "--"
                tva_value = "--"

            # --- Set pos to 0 if deal is closed, otherwise use original value ---
            deal_status = str(deal.get('status', 'ACTIVE')).upper()
            pos_value = '0' if deal_status == 'CLOSED' else deal.get(
                'pos', '1')

            cmp = price_fetcher.get_cmp(deal.get('symbol', ''))

            # Calculate values
            qty = float(deal.get('qty', 0))
            ep = float(deal.get('ep', 0))
            current_price = float(cmp if cmp is not None else 0)

            invested_amount = qty * ep
            current_value = qty * current_price
            pnl_amount = current_value - invested_amount
            pnl_percent = (pnl_amount / invested_amount *
                           100) if invested_amount > 0 else 0

            # date
            created_at = deal.get('created_at')
            date_str = '--'
            if created_at:
                try:
                    if isinstance(created_at, str):
                        if created_at.endswith('Z'):
                            created_at = created_at[:-1]
                        dt = datetime.fromisoformat(created_at)
                    else:
                        dt = created_at
                    date_str = dt.strftime('%Y-%m-%d')
                except Exception:
                    pass

            # Format deal
            formatted_deal = {
                'id': deal.get('id'),
                'trade_signal_id': trade_signal_id,
                'symbol': symbol,
                'seven': d7_val if d7_val else '--',
                'seven_percent': p7,
                'thirty': d30_val if d30_val else '--',
                'thirty_percent': p30,
                'date': date_str,
                'qty': qty,
                'ep': entry_price,
                'cmp': cmp_display,
                'pos': pos_value,
                'chan_percent': round(change_percent, 2),
                'inv': investment,
                'tp': tp_value,  # Target price with business logic
                'tpr': tpr_value,  # Target profit return percentage
                'tva': tva_value,  # Target value amount
                'pl': round(profit_loss, 2),
                'qt': qt_value,  # Symbol repeat count
                'ed': deal.get('ed', '--'),  # Exit date
                'exp': '--',  # Expiry
                'pr': '--',  # Price range
                'pp': '--',  # Performance points
                'iv': investment,  # Investment value
                'ip': entry_price,  # Entry price
                'status': deal_status,  # Use actual status from database
                'deal_type': 'MANUAL',
                'tags': '',
                'created_at': '',
                'updated_at': ''
            }

            formatted_deals.append(formatted_deal)

            # Add to totals
            total_invested += invested_amount
            total_current_value += current_value
            total_pnl += pnl_amount

        total_pnl_percent = (total_pnl / total_invested *
                             100) if total_invested > 0 else 0

        return jsonify({
            'success': True,
            'deals': formatted_deals,
            'data': formatted_deals,  # For compatibility
            'message':
            f'Successfully loaded {len(formatted_deals)} deals for user {username}',
            'summary': {
                'total_deals': len(formatted_deals),
                'total_invested': round(total_invested, 2),
                'total_current_value': round(total_current_value, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percent': round(total_pnl_percent, 2)
            }
        })

    except Exception as e:
        logger.error(f"Error in user deals API: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'deals': [],
            'summary': {
                'total_deals': 0,
                'total_invested': 0,
                'total_current_value': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0
            }
        }), 500


@deals_api.route('/deals/check-duplicate', methods=['POST'])
def check_deal_duplicate():
    """Check if a deal with the same symbol already exists"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        symbol = data.get('symbol', '').strip()
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400

        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id or not isinstance(user_id, int):
            user_id = 1

        # Check for duplicate
        is_duplicate = check_duplicate_deal(symbol, user_id)

        return jsonify({
            'success': True,
            'duplicate': is_duplicate,
            'symbol': symbol
        })

    except Exception as e:
        logger.error(f"Error checking deal duplicate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/edit-deal', methods=['POST'])
def edit_deal():
    """Edit a user deal (quantity and target price) using dynamic user tables"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        deal_id = data.get('deal_id', '').strip()
        symbol = data.get('symbol', '').strip()
        qty = data.get('qty')
        target_price = data.get('target_price')
        entry_price = data.get('entry_price')
        tpr_percent = data.get('tpr_percent')

        if not deal_id or not symbol:
            return jsonify({
                'success': False,
                'error': 'Deal ID and symbol are required'
            }), 400

        # Check if at least one field is provided for update
        fields_to_update = {}
        update_count = 0

        # Validate and collect fields to update
        if qty is not None:
            try:
                qty = float(qty)
                if qty <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Quantity must be a positive number'
                    }), 400
                fields_to_update['qty'] = qty
                update_count += 1
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid quantity value'
                }), 400

        if target_price is not None:
            try:
                target_price = float(target_price)
                if target_price <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Target price must be a positive number'
                    }), 400
                fields_to_update['target_price'] = target_price
                update_count += 1
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid target price value'
                }), 400

        if entry_price is not None:
            try:
                entry_price = float(entry_price)
                if entry_price <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Entry price must be a positive number'
                    }), 400
                fields_to_update['ep'] = entry_price  # Map to database column name
                update_count += 1
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid entry price value'
                }), 400

        if tpr_percent is not None:
            try:
                tpr_percent = float(tpr_percent)
                fields_to_update['tpr_percent'] = tpr_percent
                update_count += 1
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid TPR percentage value'
                }), 400

        # Ensure at least one field is being updated
        if update_count == 0:
            return jsonify({
                'success': False,
                'error': 'At least one field must be provided for update'
            }), 400

        # Get username from session
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username is required - please log in'
            }), 400

        # Import dynamic deals service
        import sys
        sys.path.append('scripts')
        from scripts.dynamic_user_deals import DynamicUserDealsService

        dynamic_deals_service = DynamicUserDealsService()

        # Check if user table exists
        if not dynamic_deals_service.table_exists(username):
            return jsonify({
                'success': False,
                'error': f'No deals table found for user {username}'
            }), 404

        # Update deal in user's dynamic table
        success = dynamic_deals_service.update_deal(username, deal_id, fields_to_update)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Deal not found or update failed'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Deal updated successfully for {symbol} ({update_count} field{"s" if update_count > 1 else ""} changed)',
            'deal_id': deal_id,
            'symbol': symbol,
            'updated_fields': list(fields_to_update.keys()),
            'update_count': update_count
        })

    except Exception as e:
        logger.error(f"Error editing deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/close-deal', methods=['POST'])
def close_deal():
    """Close a user deal by updating its status and exit date using dynamic user tables"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        deal_id = data.get('deal_id', '').strip()
        symbol = data.get('symbol', '').strip()
        exit_date = data.get('exit_date', '').strip()

        if not deal_id or not symbol:
            return jsonify({
                'success': False,
                'error': 'Deal ID and symbol are required'
            }), 400

        if not exit_date:
            return jsonify({
                'success': False,
                'error': 'Exit date is required'
            }), 400

        # Validate exit date format and ensure it's not in the future
        try:
            from datetime import datetime, date
            exit_date_obj = datetime.strptime(exit_date, '%Y-%m-%d').date()
            today = date.today()
            
            if exit_date_obj > today:
                return jsonify({
                    'success': False,
                    'error': 'Exit date cannot be in the future'
                }), 400
                
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid exit date format. Use YYYY-MM-DD'
            }), 400

        # Get username from session
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username is required - please log in'
            }), 400

        # Import dynamic deals service
        import sys
        sys.path.append('scripts')
        from scripts.dynamic_user_deals import DynamicUserDealsService

        dynamic_deals_service = DynamicUserDealsService()

        # Check if user table exists
        if not dynamic_deals_service.table_exists(username):
            return jsonify({
                'success': False,
                'error': f'No deals table found for user {username}'
            }), 404

        # Update deal status to CLOSED, set exit date and pos to 0
        success = dynamic_deals_service.update_deal(username, deal_id, {
            'status': 'CLOSED',
            'ed': exit_date,
            'pos': '0'
        })

        if not success:
            return jsonify({
                'success': False,
                'error': 'Deal not found or update failed'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Deal closed successfully for {symbol}',
            'deal_id': deal_id,
            'symbol': symbol,
            'status': 'CLOSED',
            'exit_date': exit_date
        })

    except Exception as e:
        logger.error(f"Error closing deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/deals/create-from-signal', methods=['POST'])
@deals_api.route('/dynamic/add-deal', methods=['POST'])
def create_deal_from_signal():
    """Create a new deal from trading signal using dynamic user tables"""
    try:
        # Import dynamic deals service
        import sys
        sys.path.append('scripts')
        from scripts.dynamic_user_deals import DynamicUserDealsService

        dynamic_deals_service = DynamicUserDealsService()

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Extract signal data
        signal_data = data.get('signal_data', {})

        # Helper functions for safe conversion
        def safe_float(value, default=0.0):
            if value is None or value == '' or value == '--':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=1):
            if value is None or value == '':
                return default
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default

        # Get username from session
        username = session.get('username')
        if not username:
            return jsonify({
                'success': False,
                'error': 'Username is required - please log in'
            }), 400

        # Get required fields with safe conversion
        symbol = signal_data.get('symbol') or signal_data.get('etf', '')
        if not symbol or symbol == 'UNKNOWN':
            return jsonify({
                'success': False,
                'error': 'Missing or invalid symbol'
            }), 400

        qty = safe_int(signal_data.get('qty'), 1)
        ep = safe_float(signal_data.get('ep'), 0.0)
        cmp = signal_data.get('cmp')

        # Handle CMP - if it's "--" or invalid, use entry price
        if cmp == "--" or cmp is None or cmp == '':
            cmp = ep
        else:
            cmp = safe_float(cmp, ep)

        pos = safe_int(signal_data.get('pos'), 1)

        # Validate required data
        if ep <= 0 or qty <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid price or quantity data'
            }), 400

        if not symbol or len(symbol.strip()) == 0:
            return jsonify({'success': False, 'error': 'Invalid symbol'}), 400

        # Check for force_add flag to bypass duplicate check
        force_add = data.get('force_add', False)

        # Check if user table exists, create if not
        if not dynamic_deals_service.table_exists(username):
            if not dynamic_deals_service.create_user_deals_table(username):
                return jsonify({
                    'success':
                    False,
                    'error':
                    f'Failed to create deals table for user {username}'
                }), 500

        # Check for duplicate unless force_add is True
        if not force_add:
            existing_deals = dynamic_deals_service.get_user_deals(username)
            for deal in existing_deals:
                if deal.get('symbol', '').upper() == symbol.upper(
                ) and deal.get('status') == 'ACTIVE':
                    return jsonify({
                        'success': False,
                        'duplicate': True,
                        'message':
                        f'This trade is already added, you want add?',
                        'symbol': symbol
                    }), 409  # Conflict status code

        # Calculate target price safely
        tp = safe_float(signal_data.get('tp'), ep * 1.05)
        if tp <= 0:
            tp = ep * 1.05

        # Calculate values
        invested_amount = ep * qty
        current_value = cmp * qty
        pnl_amount = current_value - invested_amount
        pnl_percent = (pnl_amount / invested_amount *
                       100) if invested_amount > 0 else 0

        # Prepare deal data for dynamic table
        deal_data = {
            'trade_signal_id': signal_data.get('id'),
            'symbol': symbol.upper(),
            'qty': qty,
            'ep': float(ep),
            'pos': str(pos),
            'cmp': float(cmp),
            'tp': float(tp),
            'status': 'ACTIVE',
            'invested_amount': float(invested_amount),
            'current_value': float(current_value),
            'pnl_amount': float(pnl_amount),
            'pnl_percent': float(pnl_percent),
            'deal_type': 'SIGNAL',
            'notes': f'Added from ETF signal - {symbol}',
            'tags': 'ETF,SIGNAL'
        }

        # Add deal to user-specific table
        deal_id = dynamic_deals_service.add_deal_to_user_table(
            username, deal_data)

        if deal_id:
            logger.info(
                f"✓ Created deal from signal: {symbol} - Deal ID: {deal_id} for user: {username}"
            )
            return jsonify({
                'success': True,
                'message': f'Deal created successfully for {symbol}',
                'deal_id': deal_id,
                'symbol': symbol,
                'entry_price': ep,
                'quantity': qty,
                'invested_amount': invested_amount,
                'table_name': f'{username}_deals'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to add deal to {username} table'
            }), 500

    except Exception as db_error:
        logger.error(f"Database error creating deal: {db_error}")
        signal_data_str = str(locals().get('signal_data', 'No signal data available'))
        logger.error(f"Signal data was: {signal_data_str}")
        return jsonify({
            'success': False,
            'error': f'Failed to create deal: {str(db_error)}'
        }), 500
