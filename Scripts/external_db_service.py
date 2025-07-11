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
            with self.connection.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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
                        signal['date'] = str(
                            signal['date']) if signal['date'] else ''
                    if signal.get('created_at'):
                        signal['created_at'] = signal['created_at'].strftime(
                            '%Y-%m-%d %H:%M:%S'
                        ) if signal['created_at'] else None

                    # Ensure numeric fields are properly formatted
                    numeric_fields = [
                        'pos', 'qty', 'ep', 'cmp', 'inv', 'tp', 'tva', 'pl',
                        'nt', 'qt'
                    ]

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
                    string_fields = [
                        'etf', 'symbol', 'dh', 'chan', 'tpr', 'ed', 'exp',
                        'pr', 'pp', 'iv', 'ip', 'ch'
                    ]
                    for field in string_fields:
                        if signal.get(field) is not None:
                            signal[field] = str(signal[field])
                        else:
                            signal[field] = ''

                    signals.append(signal)

                logger.info(
                    f"✓ Fetched {len(signals)} admin trade signals from external database"
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


def get_etf_signals_from_external_db():
    """Get ETF signals data from external database"""
    try:
        logging.info("Attempting to fetch ETF signals from external database")

        # Try to get from local database first
        try:
            from core.database import get_db_connection
            import psycopg2.extras

            conn = get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                    SELECT id, symbol, ep as entry_price, cmp as current_price, qty as quantity, 
                           inv as investment_amount, pos as signal_type, created_at, 
                           pl as pnl, chan as pnl_percentage, tp as target_price,
                           date, thirty, seven, dh, ch, tva, tpr, ed, exp, pr, pp, iv, ip, nt, qt
                    FROM admin_trade_signals 
                    ORDER BY created_at DESC
                    LIMIT 100
                """)

                    signals = cursor.fetchall()
                    result = []

                    for signal in signals:
                        signal_dict = dict(signal)
                        result.append(signal_dict)

                    conn.close()
                    logging.info(f"✓ Found {len(result)} signals from admin_trade_signals table")
                    return result

        except Exception as db_error:
            logging.error(f"Database error: {db_error}")

        # If no database connection, return empty list
        logging.info("No external database connection available")
        return []

    except Exception as e:
        logging.error(f"Error fetching ETF signals from external DB: {e}")
        return []


def get_basic_trade_signals_data_json():
    """Get Basic Trade signals data in JSON format for API response"""
    try:
        signals = get_etf_signals_from_external_db()
        count = 0
        formatted_signals = []

        for signal in signals:
            # Get basic trading data with proper null handling
            symbol = str(signal.get('symbol') or signal.get('etf')
                         or 'N/A').upper()
            pos = int(signal.get('pos')
                      or 1)  # Position: 1 for long, -1 for short

            # Handle numeric fields with null safety
            qty = float(signal.get('qty')
                        or 0) if signal.get('qty') is not None else 0.0
            ep = float(signal.get('ep')
                       or 0) if signal.get('ep') is not None else 0.0
            cmp = float(signal.get('cmp')
                        or 0) if signal.get('cmp') is not None else 0.0

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
                d30_value = float(d30_raw) if d30_raw is not None and str(
                    d30_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d30_value = cmp

            try:
                d7_value = float(d7_raw) if d7_raw is not None and str(
                    d7_raw).strip() != '' else cmp
            except (ValueError, TypeError):
                d7_value = cmp

            # Calculate 30-day and 7-day performance percentages
            ch30_percent = (
                (cmp - d30_value) /
                d30_value) * 100 if d30_value > 0 and cmp > 0 else 0
            ch7_percent = ((cmp - d7_value) /
                           d7_value) * 100 if d7_value > 0 and cmp > 0 else 0

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

        logger.info(
            f"✅ Formatted {count} basic trade signals for API response")

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


# def get_etf_signals_data_json():
#     """Get ETF signals data in JSON format for API response"""
#     try:
#         signals = get_etf_signals_from_external_db()
#         count = 0
#         formatted_signals = []

#         for signal in signals:
#             # Get basic trading data with proper null handling
#             symbol = str(signal.get('symbol') or signal.get('etf')
#                          or 'N/A').upper()
#             pos = int(signal.get('pos')
#                       or 1)  # Position: 1 for long, -1 for short

#             # Handle numeric fields with null safety
#             qty = float(signal.get('qty')
#                         or 0) if signal.get('qty') is not None else 0.0
#             ep = float(signal.get('ep')
#                        or 0) if signal.get('ep') is not None else 0.0
#             cmp = float(signal.get('cmp')
#                         or 0) if signal.get('cmp') is not None else 0.0

#             # Calculate investment amount (qty * ep)
#             inv = qty * ep if qty and ep else 0

#             # Calculate current value and P&L
#             current_value = qty * cmp if qty and cmp else 0
#             if pos == 1:  # Long position
#                 pl = current_value - inv  # Profit/Loss
#                 chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
#             else:  # Short position
#                 pl = inv - current_value  # Profit/Loss (reversed for short)
#                 chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0

#             # Calculate target price (assume 10% target)
#             target_percent = 10.0
#             if pos == 1:  # Long position
#                 tp = ep * (1 + target_percent / 100) if ep > 0 else 0
#             else:  # Short position
#                 tp = ep * (1 - target_percent / 100) if ep > 0 else 0

#             # Calculate target value amount and target profit
#             tva = qty * tp if qty and tp else 0
#             tPr = tva - inv if pos == 1 else inv - tva if tva > 0 else 0

#             # Get historical data for 30-day and 7-day performance with null safety
#             d30_raw = signal.get('thirty') or signal.get('d30')
#             d7_raw = signal.get('seven') or signal.get('d7')

#             # Handle null/empty values safely
#             try:
#                 d30_value = float(d30_raw) if d30_raw is not None and str(
#                     d30_raw).strip() != '' else cmp
#             except (ValueError, TypeError):
#                 d30_value = cmp

#             try:
#                 d7_value = float(d7_raw) if d7_raw is not None and str(
#                     d7_raw).strip() != '' else cmp
#             except (ValueError, TypeError):
#                 d7_value = cmp

#             # Calculate 30-day and 7-day performance percentages
#             ch30_percent = (
#                 (cmp - d30_value) /
#                 d30_value) * 100 if d30_value > 0 and cmp > 0 else 0
#             ch7_percent = ((cmp - d7_value) /
#                            d7_value) * 100 if d7_value > 0 and cmp > 0 else 0

#             # Format percentage values
#             ch30_value = f"{ch30_percent:.2f}%"
#             ch7_value = f"{ch7_percent:.2f}%"
#             chan_value = f"{chan_percent:.2f}%"

#             # Calculate total quantities and investment for this symbol
#             qt = qty  # Total quantity for this record
#             iv = inv  # Total invested value for this record
#             ip = ep  # Initial price (same as entry price)
#             nt = cmp  # Net price (same as current price)

#             # Exit fields (blank for active signals)
#             ed = signal.get('ed', '')  # Exit date
#             exp = signal.get('exp', '')  # Exit price
#             pr = signal.get('pr', '')  # Profit on exit
#             pp = signal.get('pp', '')  # Profit percentage on exit

#             formatted_signal = {
#                 'trade_signal_id': signal.get('id') or count,
#                 'id': signal.get('id') or count,
#                 'etf': symbol,
#                 'symbol': symbol,
#                 'thirty': round(d30_value, 2),
#                 'd30': round(d30_value, 2),
#                 'dh': ch30_value,
#                 'ch30': ch30_value,
#                 'seven': round(d7_value, 2),
#                 'd7': round(d7_value, 2),
#                 'ch': ch7_value,
#                 'ch7': ch7_value,
#                 'date': signal.get('date', ''),
#                 'pos': pos,
#                 'qty': int(qty),
#                 'ep': round(ep, 2),
#                 'cmp': round(cmp, 2),
#                 'chan': chan_value,
#                 'inv': round(inv, 2),
#                 'tp': round(tp, 2),
#                 'tva': round(tva, 2),
#                 'tpr': round(tPr, 2),
#                 'pl': round(pl, 2),
#                 'ed': ed,
#                 'exp': exp,
#                 'pr': pr,
#                 'pp': pp,
#                 'iv': round(iv, 2),
#                 'ip': round(ip, 2),
#                 'nt': round(nt, 2),
#                 'qt': int(qt),
#                 'created_at': signal.get('created_at', ''),
#                 # Add formatted display values
#                 'd30_formatted': f"₹{d30_value:.2f}",
#                 'd7_formatted': f"₹{d7_value:.2f}",
#                 'cmp_formatted': f"₹{cmp:.2f}",
#                 'inv_formatted': f"₹{inv:.2f}",
#                 'pl_formatted': f"₹{pl:.2f}",
#                 'tp_formatted': f"₹{tp:.2f}",
#                 'tva_formatted': f"₹{tva:.2f}",
#                 'tpr_formatted': f"₹{tPr:.2f}"
#             }
#             formatted_signals.append(formatted_signal)

#         return {
#             'data':
#             formatted_signals,
#             'recordsTotal':
#             len(formatted_signals),
#             'recordsFiltered':
#             len(formatted_signals),
#             'message':
#             f'Successfully loaded {len(formatted_signals)} signals with historical data'
#         }

#     except Exception as e:
#         logger.error(f"Error getting ETF signals data: {e}")
#         return {
#             'data': [],
#             'recordsTotal': 0,
#             'recordsFiltered': 0,
#             'error': str(e)
#         }


def get_etf_signals_data_json():
    """Get ETF signals data in JSON format with calculations"""
    try:
        signals = get_etf_signals_from_external_db()
        if not signals:
            logger.warning("No signals found in database")
            return {
                'data': [],
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'message': 'No signals found in database'
            }

        count = 0
        formatted_signals = []

        # Track symbol quantities for total quantity calculation
        symbol_quantities = {}
        symbol_counts = {}

        # First pass to calculate symbol quantities and counts
        for signal in signals:
            symbol = str(signal.get('symbol', '')).strip().upper()
            if not symbol or symbol == 'N/A':
                symbol = 'UNKNOWN'

            qty = float(signal.get('qty')
                        or 0) if signal.get('qty') is not None else 0.0

            # Track total quantity per symbol
            if symbol in symbol_quantities:
                symbol_quantities[symbol] += qty
            else:
                symbol_quantities[symbol] = qty

            # Track count of trades per symbol
            if symbol in symbol_counts:
                symbol_counts[symbol] += 1
            else:
                symbol_counts[symbol] = 1

        logger.info(f"Processing {len(signals)} signals...")
        logger.info(
            f"Found {len(symbol_counts)} unique symbols: {list(symbol_counts.keys())}"
        )

        # Process each signal
        for signal in signals:
            count += 1
            signal_id = signal.get('id')

            # Get basic trading data with proper null handling
            symbol = str(signal.get('symbol', '')).strip().upper()
            if not symbol or symbol == 'N/A':
                symbol = 'UNKNOWN'

            pos = int(signal.get('pos')
                      or 1)  # Position: 1 for long, -1 for short

            # Handle numeric fields with null safety
            qty = float(signal.get('qty')
                        or 0) if signal.get('qty') is not None else 0.0
            ep = float(signal.get('ep')
                       or 0) if signal.get('ep') is not None else 0.0
            # cmp  is to be taken from the last row close cloumn
            cmp = float(signal.get('cmp')  
                        or 0) if signal.get('cmp') is not None else 0.0
            # d7_price come from symbol_5min table  current row - 375 previous row else 0 no price, symbol_daily table  
            d7_price = float(signal.get('d7')
                             or 0) if signal.get('d7') is not None else 0.0
            # d30_price come from symbol_5min table  current row - 375 previous row else 0 no price, symbol_daily table
            d30_price = float(signal.get('d30')
                              or 0) if signal.get('d30') is not None else 0.0

            # Calculate investment amount (qty * ep)
            inv = qty * ep if qty and ep else 0

            # Calculate current value and P&L
            current_value = qty * cmp if qty and cmp else 0

            # pos is status buy and sell 1 for buy -1 for sell

            # make status column in database 1 and 0.  1 , 1 for deal is runing and 0 for deal is closed 
            # if status is 1 then show all the cloums
            # if satus 0 then hide inv, tg, pt, action hide 

            if pos == 1:  
                pl = current_value - inv  # Profit/Loss
                chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
            else:  # Short position
                pl = inv - current_value  # Profit/Loss (reversed for short)
                chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0

            # Calculate 30-day and 7-day performance percentages
            ch30_percent = (
                (cmp - d30_price) / d30_price) * 100 if d30_price > 0 else 0
            ch7_percent = (
                (cmp - d7_price) / d7_price) * 100 if d7_price > 0 else 0

            # Calculate price changes
            ch30_value = cmp - d30_price if d30_price > 0 else 0
            ch7_value = cmp - d7_price if d7_price > 0 else 0
            chan_value = cmp - ep if ep > 0 else 0

            # Calculate target price (assume 3% target)
            target_percent = 3.0
            # # tp = pos * ()
            # if pos == 1:  # Long 
            # tp = ep+ep*target_percent
            tp = ep + pos* (1 + target_percent / 100)
            # else:  # Short position
            #     tp = ep * (1 - target_percent / 100) if ep > 0 else 0

            # Calculate target value amount and target profit
            tva = qty * tp if qty and tp else 0
            tPr = tva - inv * pos 

            # Get total trades for this symbol
            qt = symbol_counts.get(symbol, 1)

            # Calculate other metrics
            iv = inv  # Total invested value for this record
            ip = ((cmp - ep) /
                  ep) * 100 if ep > 0 else 0  # Entry price percentage
            nt = cmp * symbol_quantities.get(symbol,
                                             qty)  # Net total for symbol

            # Exit fields close pos. if status is 0 and exit price and exit date . 
            #  if status change to 0 hide and show appropriate columns
            # hide = inv target profit, target vlue, action,

            ed = signal.get('ed', '')  # Exit date
            exp = signal.get('exp', '')  # Exit price

            # Calculate exit profit if exit price exists
            if exp:
                try:
                    exp_value = float(exp)
                    pr = (exp_value - ep) * qty if qty and ep else 0
                    pp = (pr / inv * 100) if inv > 0 else 0
                except (ValueError, TypeError):
                    pr = 0
                    pp = 0
            else:
                pr = 0
                pp = 0

            formatted_signal = {
                'trade_signal_id': signal_id or count,
                'id': signal_id or count,
                'symbol': symbol,
                'thirty': round(d30_price, 2),
                'd30': round(d30_price, 2),
                'dh': f"{ch30_percent:.2f}%",
                'ch30': round(ch30_value, 2),
                'seven': round(d7_price, 2),
                'd7': round(d7_price, 2),
                'ch': f"{ch7_percent:.2f}%",
                'ch7': round(ch7_value, 2),
                'date': signal.get('date', ''),
                'pos': pos,
                'qty': int(qty),
                'ep': round(ep, 2),
                'cmp': round(cmp, 2),
                'chan': round(chan_value, 2),
                'chan_percent': f"{chan_percent:.2f}%",
                'inv': round(inv, 2),
                'tp': round(tp, 2),
                'tva': round(tva, 2),
                'tpr': round(tPr, 2),
                'pl': round(pl, 2),
                'ed': ed,
                'exp': exp,
                'pr': round(pr, 2),
                'pp': f"{pp:.2f}%",
                'iv': round(iv, 2),
                'ip': round(ip, 2),
                'nt': round(nt, 2),
                'qt': qt,  # Total trades for this symbol
                'created_at': signal.get('created_at', ''),
                # Add formatted display values
                'd30_formatted': f"₹{d30_price:.2f}",
                'd7_formatted': f"₹{d7_price:.2f}",
                'cmp_formatted': f"₹{cmp:.2f}",
                'inv_formatted': f"₹{inv:.2f}",
                'pl_formatted': f"₹{pl:.2f}",
                'tp_formatted': f"₹{tp:.2f}",
                'tva_formatted': f"₹{tva:.2f}",
                'tpr_formatted': f"₹{tPr:.2f}",
                'total_symbol_quantity': symbol_quantities.get(symbol, qty),
                'total_symbol_trades': qt,
            }
            formatted_signals.append(formatted_signal)

            logger.info(f"Processed signal {count}/{len(signals)} - {symbol}")

        total_signals = len(formatted_signals)
        success_message = f"✅ Successfully processed {total_signals} signals."

        logger.info(success_message)

        return {
            'data': formatted_signals,
            'recordsTotal': total_signals,
            'recordsFiltered': total_signals,
            'message': success_message,
            'symbol_stats': {
                'total_unique_symbols': len(symbol_counts),
                'symbol_trade_counts': symbol_counts,
                'symbol_quantities': symbol_quantities
            }
        }

    except Exception as e:
        logger.error(f"❌ Error getting ETF signals data: {e}")
        return {
            'data': [],
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'error': str(e),
            'message': f'❌ Error loading signals: {str(e)}'
        }