"""
External Database Service for fetching data from admin_trade_signals table
Connects to external PostgreSQL database and provides ETF signals data
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
        """Fetch all admin trade signals from external database"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                query = """
                SELECT 
                    id,
                    etf,
                    symbol,
                    thirty,
                    dh,
                    date,
                    pos,
                    qty,
                    ep,
                    cmp,
                    chan,
                    inv,
                    tp,
                    tva,
                    tpr,
                    pl,
                    ed,
                    exp,
                    pr,
                    pp,
                    iv,
                    ip,
                    nt,
                    qt,
                    seven,
                    ch,
                    created_at
                FROM admin_trade_signals 
                ORDER BY created_at DESC
                """

                cursor.execute(query)
                results = cursor.fetchall()

                # Convert RealDictRow to regular dict and handle data types
                signals = []
                for row in results:
                    signal = dict(row)

                    # Convert dates to string if they exist
                    if signal.get('date'):
                        signal['date'] = str(signal['date']) if signal['date'] else ''
                    if signal.get('created_at'):
                        signal['created_at'] = signal['created_at'].strftime('%Y-%m-%d %H:%M:%S') if signal['created_at'] else None

                    # Ensure numeric fields are properly formatted
                    numeric_fields = ['pos', 'qty', 'ep', 'cmp', 'inv', 'tp', 'tva', 'pl', 'nt', 'qt']

                    for field in numeric_fields:
                        if signal.get(field) is not None:
                            try:
                                signal[field] = float(signal[field])
                            except (ValueError, TypeError):
                                signal[field] = 0.0

                    # Handle performance fields specifically
                    performance_fields = ['thirty', 'seven']
                    for field in performance_fields:
                        if signal.get(field) is not None:
                            try:
                                signal[field] = float(signal[field])
                            except (ValueError, TypeError):
                                signal[field] = 0.0
                        else:
                            signal[field] = 0.0

                    # Ensure string fields are properly formatted
                    string_fields = ['etf', 'symbol', 'dh', 'chan', 'tpr', 'ed', 'exp', 'pr', 'pp', 'iv', 'ip', 'ch']
                    for field in string_fields:
                        if signal.get(field) is not None:
                            signal[field] = str(signal[field])
                        else:
                            signal[field] = ''

                    signals.append(signal)

                logger.info(f"✓ Fetched {len(signals)} admin trade signals from external database")
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
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            query = """
            SELECT * FROM admin_trade_signals 
            WHERE id = %s
            """

            cursor.execute(query, (signal_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                signal = dict(result)
                # Format dates and numeric fields same as above
                if signal.get('entry_date'):
                    signal['entry_date'] = signal['entry_date'].strftime('%Y-%m-%d') if signal['entry_date'] else None
                if signal.get('exit_date'):
                    signal['exit_date'] = signal['exit_date'].strftime('%Y-%m-%d') if signal['exit_date'] else None

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

def get_etf_signals_data_json():
    """Get ETF signals data in JSON format for API response"""
    try:
        signals = get_etf_signals_from_external_db()
        count = 0
        formatted_signals = []

        for signal in signals:
            # Get d30 and ch30 values with proper handling
            d30_value = signal.get('thirty') or signal.get('d30') or 0
            ch30_value = signal.get('dh') or signal.get('ch30') or '0.00%'
            d7_value = signal.get('seven') or signal.get('d7') or 0  
            ch7_value = signal.get('ch') or signal.get('ch7') or '0.00%'

            # Convert to proper types
            try:
                d30_value = float(d30_value) if d30_value else 0.0
                d7_value = float(d7_value) if d7_value else 0.0
            except (ValueError, TypeError):
                d30_value = 0.0
                d7_value = 0.0

            # Ensure percentage values are properly formatted
            if isinstance(ch30_value, (int, float)):
                ch30_value = f"{ch30_value:.2f}%"
            elif isinstance(ch30_value, str) and not ch30_value.endswith('%'):
                try:
                    ch30_value = f"{float(ch30_value):.2f}%"
                except (ValueError, TypeError):
                    ch30_value = "0.00%"

            if isinstance(ch7_value, (int, float)):
                ch7_value = f"{ch7_value:.2f}%"
            elif isinstance(ch7_value, str) and not ch7_value.endswith('%'):
                try:
                    ch7_value = f"{float(ch7_value):.2f}%"
                except (ValueError, TypeError):
                    ch7_value = "0.00%"

            formatted_signal = {
                'trade_signal_id': signal.get('id') or count,
                'id': signal.get('id') or count,
                'etf': signal.get('etf') or signal.get('symbol') or 'N/A',
                'symbol': signal.get('symbol') or signal.get('etf') or 'N/A',
                'thirty': float(d30_value) if d30_value else 0.0,
                'd30': float(d30_value) if d30_value else 0.0,
                'dh': ch30_value,
                'ch30': ch30_value,
                'seven': float(d7_value) if d7_value else 0.0,
                'd7': float(d7_value) if d7_value else 0.0,
                'ch': ch7_value,
                'ch7': ch7_value,
                'date': signal.get('date', ''),
                'pos': signal.get('pos', 0),
                'qty': signal.get('qty', 0),
                'ep': signal.get('ep', 0),
                'cmp': signal.get('cmp', 0),
                'chan': signal.get('chan', ''),
                'inv': signal.get('inv', 0),
                'tp': signal.get('tp', 0),
                'tva': signal.get('tva', 0),
                'tpr': signal.get('tpr', ''),
                'pl': signal.get('pl', 0),
                'ed': signal.get('ed', ''),
                'exp': signal.get('exp', ''),
                'pr': signal.get('pr', ''),
                'pp': signal.get('pp', ''),
                'iv': signal.get('iv', ''),
                'ip': signal.get('ip', ''),
                'nt': signal.get('nt', 0),
                'qt': signal.get('qt', 0),
                'created_at': signal.get('created_at', ''),
                # Add formatted display values
                'd30_formatted': f"₹{d30_value:.2f}" if d30_value else "₹0.00",
                'd7_formatted': f"₹{d7_value:.2f}" if d7_value else "₹0.00",
                'cmp_formatted': f"₹{signal.get('cmp', 0):.2f}" if signal.get('cmp') else "₹0.00"
            }
            formatted_signals.append(formatted_signal)

        return {
            'data': formatted_signals,
            'recordsTotal': len(formatted_signals),
            'recordsFiltered': len(formatted_signals),
            'message': f'Successfully loaded {len(formatted_signals)} signals with historical data'
        }

    except Exception as e:
        logger.error(f"Error getting ETF signals data: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'error': str(e)
        }