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
        """Fetch only required fields from admin_trade_signals with CMP from symbols table"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            with self.connection.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get only required fields from admin_trade_signals and match with symbols table for CMP
                query = """
                SELECT 
                    ats.id,
                    ats.symbol,
                    ats.qty,
                    ats.ep as entry_price,
                    ats.created_at,
                    ats.date,
                    ats.pos,
                    COALESCE(s.close, 0) as cmp
                FROM admin_trade_signals ats
                LEFT JOIN symbols s ON UPPER(TRIM(ats.symbol)) = UPPER(TRIM(s.symbol))
                ORDER BY ats.created_at DESC
                """

                cursor.execute(query)
                results = cursor.fetchall()

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
                    numeric_fields = ['pos', 'qty', 'entry_price', 'cmp']

                    for field in numeric_fields:
                        if signal.get(field) is not None:
                            try:
                                signal[field] = float(signal[field])
                            except (ValueError, TypeError):
                                signal[field] = 0.0

                    # Ensure string fields are properly formatted
                    if signal.get('symbol'):
                        signal['symbol'] = str(signal['symbol']).upper()
                    else:
                        signal['symbol'] = ''

                    signals.append(signal)

                logger.info(
                    f"✓ Fetched {len(signals)} admin trade signals with CMP from symbols table"
                )
                return signals

        except Exception as e:
            logger.error(f"Error fetching admin trade signals: {e}")
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
        formatted_signals = []
        count = 0

        for signal in signals:
            count += 1
            # Get only the 4 required fields from admin_trade_signals
            symbol = str(signal.get('symbol') or 'N/A').upper()
            qty = float(signal.get('qty') or 0) if signal.get('qty') is not None else 0.0
            entry_price = float(signal.get('entry_price') or 0) if signal.get('entry_price') is not None else 0.0
            
            # Get CMP from symbols table (fetched via JOIN query)
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
            'message': f'Successfully loaded {len(paginated_signals)} signals from admin_trade_signals with CMP from symbols table'
        }

    except Exception as e:
        logger.error(f"Error getting ETF signals data: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'page': page,
            'page_size': page_size,
            'has_more': False,
            'error': str(e)
        }
