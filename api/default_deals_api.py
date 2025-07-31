from flask import Blueprint, jsonify, request
import logging
from Scripts.external_db_service import SignalsFetcher, PriceFetcher, HistoricalFetcher, DatabaseConnector
import pandas as pd
from datetime import datetime

# Create blueprint
default_deals_api = Blueprint('default_deals_api', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def try_percent(current, historical):
    """Calculate percentage change"""
    try:
        if historical and historical != '--' and current and current != '--':
            current_val = float(current)
            hist_val = float(historical)
            if hist_val > 0:
                return round(((current_val - hist_val) / hist_val) * 100, 2)
    except:
        pass
    return '--'


@default_deals_api.route('/api/default-deals', methods=['GET'])
def get_default_deals():
    """
    Get all default deals data from admin_trade_signals table
    No authentication required - shows all trading signals for everyone
    """
    try:
        logger.info(
            "📊 Fetching default deals data from admin_trade_signals...")

        # Get external database connection using centralized config
        try:
            from config.database_config import get_db_connection
            conn = get_db_connection()
            if not conn:
                raise Exception("Failed to get database connection")
            db_connector = DatabaseConnector()
            db_connector._connection = conn  # Use the centralized connection
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            db_connector = None

        if not db_connector:
            logger.error("❌ Failed to connect to external database")
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            }), 500

        try:
            # Query to get all trading signals from admin_trade_signals table
            query = """
            SELECT 
                id,
                symbol,
                qty,
                ep,
                pos,
                created_at
            FROM admin_trade_signals 
            ORDER BY created_at DESC
            """

            deals_data = db_connector.execute_query(query)

            if not deals_data:
                return jsonify({
                    'success': True,
                    'message': 'No trading signals found',
                    'deals': [],
                    'summary': {
                        'total_deals': 0,
                        'total_invested': 0,
                        'total_current_value': 0,
                        'total_pnl': 0,
                        'total_pnl_percent': 0
                    }
                })

            # Initialize fetcher objects
            price_fetcher = PriceFetcher(db_connector)
            signals_fetcher = SignalsFetcher(db_connector)
            hist_fetcher = HistoricalFetcher(db_connector)

            # Format deals for frontend
            formatted_deals = []
            total_invested = 0
            total_current_value = 0
            total_pnl = 0
            symbol_counts = {}

            for deal in deals_data:
                # Extract basic trading info
                symbol = str(deal.get('symbol') or 'N/A').upper()
                trade_signal_id = deal.get('id')
                qty = float(deal.get('qty') or 0)
                entry_price = float(deal.get('ep') or 0)

                # Symbol repeat count
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
                qt_value = symbol_counts[symbol]

                # Format the date
                raw_date = deal.get('created_at', '')
                if raw_date:
                    try:
                        if isinstance(raw_date, str):
                            dt_obj = pd.to_datetime(raw_date)
                        else:
                            dt_obj = raw_date
                        date_fmt = dt_obj.strftime("%d-%m-%y %H:%M")
                        date_str = dt_obj.strftime('%Y-%m-%d')
                    except Exception:
                        date_fmt = str(raw_date)
                        date_str = '--'
                else:
                    date_fmt = ''
                    date_str = '--'

                # Fetch prices (CMP, 7D, 30D)
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

                # Investment/Profit/Loss calculations
                investment = qty * entry_price
                current_value = qty * cmp_numeric if cmp_is_num else 0
                profit_loss = current_value - investment if cmp_is_num else 0
                change_percent = (
                    (cmp_numeric - entry_price) /
                    entry_price) * 100 if cmp_is_num and entry_price > 0 else 0

                # Target Price calculation (business logic)
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

                # Position value (default to 1 for active deals, 0 for closed)
                pos_value = deal.get('pos', 1)
                if pos_value is None:
                    pos_value = 1

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
                    'ed':
                    '--',  # Exit date (not applicable for trading signals)
                    'exp': '--',  # Expiry
                    'pr': '--',  # Price range
                    'pp': '--',  # Performance points
                    'iv': investment,  # Investment value
                    'ip': entry_price,  # Entry price
                    'status': 'ACTIVE',  # Default status for trading signals
                    'deal_type': 'SIGNAL',
                    'tags': '',
                    'created_at': date_fmt,
                    'updated_at': ''
                }

                formatted_deals.append(formatted_deal)

                # Add to totals
                total_invested += investment
                total_current_value += current_value
                total_pnl += profit_loss

            total_pnl_percent = (total_pnl / total_invested *
                                 100) if total_invested > 0 else 0

            db_connector.disconnect()

            return jsonify({
                'success': True,
                'deals': formatted_deals,
                'data': formatted_deals,  # For compatibility
                'message':
                f'Successfully loaded {len(formatted_deals)} trading signals',
                'summary': {
                    'total_deals': len(formatted_deals),
                    'total_invested': round(total_invested, 2),
                    'total_current_value': round(total_current_value, 2),
                    'total_pnl': round(total_pnl, 2),
                    'total_pnl_percent': round(total_pnl_percent, 2)
                }
            })

        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            db_connector.disconnect()
            return jsonify({
                'success': False,
                'message': f'Database query error: {str(e)}',
                'deals': [],
                'summary': {
                    'total_deals': 0,
                    'total_invested': 0,
                    'total_current_value': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0
                }
            }), 500

    except Exception as e:
        logger.error(f"❌ Error in get_default_deals: {e}")
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


@default_deals_api.route('/api/default-edit-deal', methods=['POST'])
def edit_default_deal():
    """API endpoint to edit a default deal in admin_trade_signals table"""
    try:
        data = request.get_json()
        deal_id = data.get('deal_id')
        symbol = data.get('symbol')
        entry_price = data.get('entry_price')
        target_price = data.get('target_price')

        if not all([deal_id, symbol, entry_price, target_price]):
            return jsonify({
                "success":
                False,
                "error":
                "Missing required fields: deal_id, symbol, entry_price, target_price"
            }), 400

        # Import and use DatabaseConnector for updates
        from Scripts.external_db_service import DatabaseConnector

        db_connector = DatabaseConnector()
        if not db_connector.connect():
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500

        try:
            # Update the admin_trade_signals record (using ep for entry_price)
            update_query = """
                UPDATE admin_trade_signals 
                SET ep = %s
                WHERE id = %s AND symbol = %s
            """

            cursor = db_connector.connection.cursor()
            cursor.execute(update_query, (entry_price, deal_id, symbol))
            db_connector.connection.commit()

            if cursor.rowcount > 0:
                logger.info(
                    f"✅ Successfully updated deal {deal_id} for symbol {symbol}"
                )
                cursor.close()

                return jsonify({
                    "success":
                    True,
                    "message":
                    f"Deal updated successfully for {symbol}"
                }), 200
            else:
                cursor.close()
                return jsonify({
                    "success": False,
                    "error": "Deal not found or no changes made"
                }), 404
        finally:
            db_connector.disconnect()

    except Exception as e:
        logger.error(f"❌ Error editing default deal: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to edit deal: {str(e)}"
        }), 500


@default_deals_api.route('/api/default-close-deal', methods=['POST'])
def close_default_deal():
    """API endpoint to close a default deal by setting pos to 0"""
    try:
        data = request.get_json()
        deal_id = data.get('deal_id')
        symbol = data.get('symbol')

        if not all([deal_id, symbol]):
            return jsonify({
                "success": False,
                "error": "Missing required fields: deal_id, symbol"
            }), 400

        # Import and use DatabaseConnector for updates
        from Scripts.external_db_service import DatabaseConnector

        db_connector = DatabaseConnector()
        if not db_connector.connect():
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500

        try:
            # Update the admin_trade_signals record to set pos = 0 (closed)
            update_query = """
                UPDATE admin_trade_signals 
                SET pos = 0
                WHERE id = %s AND symbol = %s
            """

            cursor = db_connector.connection.cursor()
            cursor.execute(update_query, (deal_id, symbol))
            db_connector.connection.commit()

            if cursor.rowcount > 0:
                logger.info(
                    f"✅ Successfully closed deal {deal_id} for symbol {symbol}"
                )
                cursor.close()

                return jsonify({
                    "success":
                    True,
                    "message":
                    f"Deal closed successfully for {symbol}"
                }), 200
            else:
                cursor.close()
                return jsonify({
                    "success": False,
                    "error": "Deal not found or already closed"
                }), 404
        finally:
            db_connector.disconnect()

    except Exception as e:
        logger.error(f"❌ Error closing default deal: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to close deal: {str(e)}"
        }), 500
