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

sys.path.append('Scripts')
from db_connector import DatabaseConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Get connection to external PostgreSQL database"""
    try:
        database_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db"
        conn = psycopg2.connect(database_url)
        logger.info("✓ Connected to external PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to external database: {e}")
        return None


def check_duplicate_deal(symbol, user_id=1):
    """
    Check if a deal with the same symbol already exists for the user
    Returns True if duplicate exists, False otherwise
    """
    try:
        conn = get_external_db_connection()
        if not conn:
            return False

        with conn.cursor() as cursor:
            query = """
            SELECT COUNT(*) FROM public.user_deals 
            WHERE symbol = %s AND user_id = %s AND status = 'ACTIVE'
            """
            cursor.execute(query, (symbol.upper(), user_id))
            count = cursor.fetchone()[0]

        conn.close()
        return count > 0

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
        # 1. Connect to external database
        external_db_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db"
        db_connector = DatabaseConnector(external_db_url)
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
                'pos': deal.get('pos', '1'),
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
                'status': deal.get('status', 'ACTIVE'),  # Use actual status from database
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


@deals_api.route('/user-deals-data')
@deals_api.route('/user-deals')
def get_user_deals_data():
    """API endpoint to get user deals data using the new get_all_deals_data_metrics function"""
    try:
        deals = get_all_deals_data_metrics()

        if not deals:
            return jsonify({
                'success': True,
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            })

        # Calculate summary from deals
        total_invested = sum(deal.get('inv', 0) for deal in deals)
        total_current = sum(
            deal.get('qty', 0) *
            deal.get('cmp', 0) if isinstance(deal.get('cmp'), (int,
                                                               float)) else 0
            for deal in deals)
        total_pnl = sum(deal.get('pl', 0) for deal in deals)
        total_pnl_percent = (total_pnl / total_invested *
                             100) if total_invested > 0 else 0

        return jsonify({
            'success': True,
            'deals': deals,
            'summary': {
                'total_deals': len(deals),
                'total_invested': total_invested,
                'total_current_value': total_current,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent
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
    """Edit a user deal (entry price and target price)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        deal_id = data.get('deal_id', '').strip()
        symbol = data.get('symbol', '').strip()
        entry_price = data.get('entry_price')
        target_price = data.get('target_price')

        if not deal_id or not symbol:
            return jsonify({
                'success': False,
                'error': 'Deal ID and symbol are required'
            }), 400

        if not entry_price or not target_price:
            return jsonify({
                'success': False,
                'error': 'Entry price and target price are required'
            }), 400

        try:
            entry_price = float(entry_price)
            target_price = float(target_price)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid price values'
            }), 400

        if entry_price <= 0 or target_price <= 0:
            return jsonify({
                'success': False,
                'error': 'Prices must be positive'
            }), 400

        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id or not isinstance(user_id, int):
            user_id = 1

        # Connect to database
        db_connector = DatabaseConnector(os.environ.get('DATABASE_URL'))

        # Update deal in database
        update_query = """
            UPDATE user_deals 
            SET entry_price = %s, target_price = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s AND symbol = %s
        """

        result = db_connector.execute_query(
            update_query,
            (entry_price, target_price, deal_id, user_id, symbol))

        if result == 0:
            return jsonify({
                'success': False,
                'error': 'Deal not found or not authorized'
            }), 404

        db_connector.close()

        return jsonify({
            'success': True,
            'message': f'Deal updated successfully for {symbol}',
            'deal_id': deal_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'target_price': target_price
        })

    except Exception as e:
        logger.error(f"Error editing deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@deals_api.route('/close-deal', methods=['POST'])
def close_deal():
    """Close a user deal by updating its status"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        deal_id = data.get('deal_id', '').strip()
        symbol = data.get('symbol', '').strip()

        if not deal_id or not symbol:
            return jsonify({
                'success': False,
                'error': 'Deal ID and symbol are required'
            }), 400

        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id or not isinstance(user_id, int):
            user_id = 1

        # Connect to database
        db_connector = DatabaseConnector(os.environ.get('DATABASE_URL'))

        # Update deal status to CLOSED and set exit date
        update_query = """
            UPDATE user_deals 
            SET status = 'CLOSED', ed = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s AND symbol = %s
        """

        result = db_connector.execute_query(update_query,
                                            (deal_id, user_id, symbol))

        if result == 0:
            return jsonify({
                'success': False,
                'error': 'Deal not found or not authorized'
            }), 404

        db_connector.close()

        return jsonify({
            'success': True,
            'message': f'Deal closed successfully for {symbol}',
            'deal_id': deal_id,
            'symbol': symbol,
            'status': 'CLOSED'
        })

    except Exception as e:
        logger.error(f"Error closing deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    


@deals_api.route('/deals/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a new deal from trading signal with duplicate detection"""
    try:
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

        # Set user_id - handle both string and integer user_ids safely
        session_user_id = session.get('user_id', 1)

        # Convert user_id to integer safely, fallback to 1 if invalid
        try:
            if isinstance(session_user_id, str):
                if session_user_id.isdigit():
                    user_id = int(session_user_id)
                else:
                    logger.info(
                        f"Non-numeric user_id in session: {session_user_id}, using default user_id = 1"
                    )
                    user_id = 1
            elif isinstance(session_user_id, int):
                user_id = session_user_id
            else:
                user_id = 1
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid user_id in session: {session_user_id}, using default user_id = 1"
            )
            user_id = 1

        # Check for force_add flag to bypass duplicate check
        force_add = data.get('force_add', False)

        # Check for duplicate unless force_add is True
        if not force_add and check_duplicate_deal(symbol, user_id):
            return jsonify({
                'success': False,
                'duplicate': True,
                'message': f'This trade is already added, you want add?',
                'symbol': symbol
            }), 409  # Conflict status code

        # Validate required data
        if ep <= 0 or qty <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid price or quantity data'
            }), 400

        if not symbol or len(symbol.strip()) == 0:
            return jsonify({'success': False, 'error': 'Invalid symbol'}), 400

        if user_id <= 0:
            return jsonify({'success': False, 'error': 'Invalid user ID'}), 400

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

        # Connect to external database
        conn = get_external_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'External database connection failed'
            }), 500

        # Ensure user_id is positive
        if not user_id or user_id <= 0:
            user_id = 1

        try:
            with conn.cursor() as cursor:
                # Insert new deal into public.user_deals table
                insert_query = """
                INSERT INTO public.user_deals (
                    user_id, symbol, trading_symbol, entry_date, position_type,
                    quantity, entry_price, current_price, target_price, stop_loss,
                    invested_amount, current_value, pnl_amount, pnl_percent,
                    status, deal_type, notes, tags, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
                """

                values = (
                    user_id,
                    symbol.upper(),
                    symbol.upper(),
                    datetime.now().strftime('%Y-%m-%d'),
                    'LONG' if pos == 1 else 'SHORT',
                    qty,
                    float(ep),
                    float(cmp),
                    float(tp),
                    float(ep * 0.95),  # Default 5% stop loss
                    float(invested_amount),
                    float(current_value),
                    float(pnl_amount),
                    float(pnl_percent),
                    'ACTIVE',
                    'SIGNAL',
                    f'Added from ETF signal - {symbol}',
                    'ETF,SIGNAL',
                    datetime.now(),
                    datetime.now())

                logger.info(f"Executing insert query with values: {values}")
                cursor.execute(insert_query, values)
                deal_id = cursor.fetchone()[0]
                conn.commit()

                logger.info(
                    f"✓ Created deal from signal: {symbol} - Deal ID: {deal_id} for user: {user_id}"
                )

                return jsonify({
                    'success': True,
                    'message': f'Deal created successfully for {symbol}',
                    'deal_id': deal_id,
                    'symbol': symbol,
                    'entry_price': ep,
                    'quantity': qty,
                    'invested_amount': invested_amount
                })

        finally:
            if conn:
                conn.close()

    except Exception as db_error:
        logger.error(f"Database error creating deal: {db_error}")
        logger.error(f"Signal data was: {signal_data}")
        logger.error(
            f"Processed values were: user_id={user_id}, symbol={symbol}, qty={qty}, ep={ep}, cmp={cmp}"
        )
        return jsonify({
            'success': False,
            'error': f'Failed to create deal: {str(db_error)}'
        }), 500
