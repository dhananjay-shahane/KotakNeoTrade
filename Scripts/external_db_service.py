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

def get_basic_trade_signals_data_json():
    """Get Basic Trade signals data in JSON format for API response"""
    try:
        signals = get_etf_signals_from_external_db()
        count = 0
        formatted_signals = []

        for signal in signals:
            # Get basic trading data with proper null handling
            symbol = str(signal.get('symbol') or signal.get('etf') or 'N/A').upper()
            pos = int(signal.get('pos') or 1)  # Position: 1 for long, -1 for short
            
            # Handle numeric fields with null safety
            qty = float(signal.get('qty') or 0) if signal.get('qty') is not None else 0.0
            ep = float(signal.get('ep') or 0) if signal.get('ep') is not None else 0.0
            cmp = float(signal.get('cmp') or 0) if signal.get('cmp') is not None else 0.0
            
            # Calculate investment amount (qty * ep)
            inv = qty * ep if qty and ep else 0
            
            # Calculate current value and P&L
            current_value = qty * cmp if qty and cmp else 0
            if pos == 1:  # Long position
                pl = current_value - inv  # Profit/Loss
                chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
            else:  # Short position
                pl = inv - current_value  # Profit/Loss (reversed for short)
                chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0
            
            # Get historical data for 30-day and 7-day performance with null safety
            d30_raw = signal.get('thirty') or signal.get('d30')
            d7_raw = signal.get('seven') or signal.get('d7')
            
            # Handle null/empty values safely
            try:
                d30_value = float(d30_raw) if d30_raw is not None and str(d30_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d30_value = cmp
                
            try:
                d7_value = float(d7_raw) if d7_raw is not None and str(d7_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d7_value = cmp
            
            # Calculate 30-day and 7-day performance percentages
            ch30_percent = ((cmp - d30_value) / d30_value) * 100 if d30_value > 0 and cmp > 0 else 0
            ch7_percent = ((cmp - d7_value) / d7_value) * 100 if d7_value > 0 and cmp > 0 else 0
            
            # Format percentage values
            ch30_value = f"{ch30_percent:.2f}"
            ch7_value = f"{ch7_percent:.2f}"
            chan_value = f"{chan_percent:.2f}"
            
            # Create basic trade signal record
            basic_signal = {
                'id': signal.get('id', count + 1),
                'etf': symbol,
                'symbol': symbol,
                'thirty': d30_value,
                'dh': ch30_value,
                'date': str(signal.get('date', '')),
                'qty': qty,
                'ep': ep,
                'cmp': cmp,
                'chan': chan_value,
                'inv': inv,
                'pl': pl,
                'seven': d7_value,
                'ch': ch7_value,
                'pos': pos
            }
            
            formatted_signals.append(basic_signal)
            count += 1

        logger.info(f"✅ Formatted {count} basic trade signals for API response")

        return {
            'success': True,
            'signals': formatted_signals,
            'total_count': count,
            'message': f'Successfully loaded {count} basic trade signals'
        }

    except Exception as e:
        logger.error(f"Error formatting basic trade signals data: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'signals': [],
            'total_count': 0,
            'error': str(e),
            'message': 'Failed to load basic trade signals data'
        }

def get_etf_signals_data_json():
    """Get ETF signals data in JSON format for API response"""
    try:
        signals = get_etf_signals_from_external_db()
        count = 0
        formatted_signals = []

        for signal in signals:
            # Get basic trading data with proper null handling
            symbol = str(signal.get('symbol') or signal.get('etf') or 'N/A').upper()
            pos = int(signal.get('pos') or 1)  # Position: 1 for long, -1 for short
            
            # Handle numeric fields with null safety
            qty = float(signal.get('qty') or 0) if signal.get('qty') is not None else 0.0
            ep = float(signal.get('ep') or 0) if signal.get('ep') is not None else 0.0
            cmp = float(signal.get('cmp') or 0) if signal.get('cmp') is not None else 0.0
            
            # Calculate investment amount (qty * ep)
            inv = qty * ep if qty and ep else 0
            
            # Calculate current value and P&L
            current_value = qty * cmp if qty and cmp else 0
            if pos == 1:  # Long position
                pl = current_value - inv  # Profit/Loss
                chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
            else:  # Short position
                pl = inv - current_value  # Profit/Loss (reversed for short)
                chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0
            
            # Calculate target price (assume 10% target)
            target_percent = 10.0
            if pos == 1:  # Long position
                tp = ep * (1 + target_percent / 100) if ep > 0 else 0
            else:  # Short position
                tp = ep * (1 - target_percent / 100) if ep > 0 else 0
            
            # Calculate target value amount and target profit
            tva = qty * tp if qty and tp else 0
            tPr = tva - inv if pos == 1 else inv - tva if tva > 0 else 0
            
            # Get historical data for 30-day and 7-day performance with null safety
            d30_raw = signal.get('thirty') or signal.get('d30')
            d7_raw = signal.get('seven') or signal.get('d7')
            
            # Handle null/empty values safely
            try:
                d30_value = float(d30_raw) if d30_raw is not None and str(d30_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d30_value = cmp
                
            try:
                d7_value = float(d7_raw) if d7_raw is not None and str(d7_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d7_value = cmp
            
            # Calculate 30-day and 7-day performance percentages
            ch30_percent = ((cmp - d30_value) / d30_value) * 100 if d30_value > 0 and cmp > 0 else 0
            ch7_percent = ((cmp - d7_value) / d7_value) * 100 if d7_value > 0 and cmp > 0 else 0
            
            # Format percentage values
            ch30_value = f"{ch30_percent:.2f}%"
            ch7_value = f"{ch7_percent:.2f}%"
            chan_value = f"{chan_percent:.2f}%"
            
            # Calculate total quantities and investment for this symbol
            qt = qty  # Total quantity for this record
            iv = inv  # Total invested value for this record
            ip = ep   # Initial price (same as entry price)
            nt = cmp  # Net price (same as current price)
            
            # Exit fields (blank for active signals)
            ed = signal.get('ed', '')  # Exit date
            exp = signal.get('exp', '')  # Exit price
            pr = signal.get('pr', '')   # Profit on exit
            pp = signal.get('pp', '')   # Profit percentage on exit

            formatted_signal = {
                'trade_signal_id': signal.get('id') or count,
                'id': signal.get('id') or count,
                'etf': symbol,
                'symbol': symbol,
                'thirty': round(d30_value, 2),
                'd30': round(d30_value, 2),
                'dh': ch30_value,
                'ch30': ch30_value,
                'seven': round(d7_value, 2),
                'd7': round(d7_value, 2),
                'ch': ch7_value,
                'ch7': ch7_value,
                'date': signal.get('date', ''),
                'pos': pos,
                'qty': int(qty),
                'ep': round(ep, 2),
                'cmp': round(cmp, 2),
                'chan': chan_value,
                'inv': round(inv, 2),
                'tp': round(tp, 2),
                'tva': round(tva, 2),
                'tpr': round(tPr, 2),
                'pl': round(pl, 2),
                'ed': ed,
                'exp': exp,
                'pr': pr,
                'pp': pp,
                'iv': round(iv, 2),
                'ip': round(ip, 2),
                'nt': round(nt, 2),
                'qt': int(qt),
                'created_at': signal.get('created_at', ''),
                # Add formatted display values
                'd30_formatted': f"₹{d30_value:.2f}",
                'd7_formatted': f"₹{d7_value:.2f}",
                'cmp_formatted': f"₹{cmp:.2f}",
                'inv_formatted': f"₹{inv:.2f}",
                'pl_formatted': f"₹{pl:.2f}",
                'tp_formatted': f"₹{tp:.2f}",
                'tva_formatted': f"₹{tva:.2f}",
                'tpr_formatted': f"₹{tPr:.2f}"
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