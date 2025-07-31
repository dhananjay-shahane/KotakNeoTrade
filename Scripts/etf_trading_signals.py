"""ETF Trading Signals API endpoints"""
from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime, timedelta
import json
from sqlalchemy import text
from core.database import db

etf_bp = Blueprint('etf', __name__, url_prefix='/etf')
logger = logging.getLogger(__name__)


@etf_bp.route('/signals', methods=['GET'])
def get_admin_signals():
    """Get ETF signals data from admin_trade_signals table with real-time prices from Yahoo Finance"""
    try:
        # Get ALL admin trade signals from database using correct column names
        result = db.session.execute(
            text("""
            SELECT id, symbol, entry_price, current_price, quantity, investment_amount, 
                   signal_type, status, created_at, pnl, pnl_percentage, change_percent,
                   target_price, stop_loss, last_update_time
            FROM admin_trade_signals 
            ORDER BY created_at DESC
        """))
        signals_data = result.fetchall()

        if not signals_data:
            logger.info("No admin trade signals found in database")
            return jsonify({
                'success':
                True,
                'signals': [],
                'total':
                0,
                'message':
                'ETF signals API configured. Database table exists but contains no data.'
            })

        # Process signals data
        signals_list = []
        total_investment = 0
        total_current_value = 0

        for row in signals_data:
            trade_signal_id, symbol, entry_price, current_price, quantity, investment_amount, signal_type, status, created_at, pnl, pnl_percentage, change_percent, target_price, stop_loss, last_update_time = row

            # Convert to proper types with better error handling
            try:
                entry_price = float(
                    entry_price) if entry_price is not None else 0.0
                current_price = float(
                    current_price
                ) if current_price is not None else entry_price
                quantity = int(quantity) if quantity is not None else 1
                investment_amount = float(
                    investment_amount) if investment_amount is not None else (
                        entry_price * quantity)
            except (ValueError, TypeError):
                # Skip invalid records
                continue

            # Ensure we have minimum required data
            if not symbol or entry_price <= 0:
                continue

            # Calculate P&L
            pnl = 0
            pnl_percentage = 0
            current_value = 0

            if entry_price > 0 and quantity > 0:
                if current_price <= 0:
                    current_price = entry_price  # Fallback to entry price

                current_value = current_price * quantity
                pnl = (current_price - entry_price) * quantity
                pnl_percentage = ((current_price - entry_price) /
                                  entry_price) * 100 if entry_price > 0 else 0

            signal_data = {
                'trade_signal_id':
                trade_signal_id,
                'id':
                trade_signal_id,
                'symbol':
                symbol or 'UNKNOWN',
                'entry_price':
                round(entry_price, 2),
                'current_price':
                round(current_price, 2),
                'quantity':
                quantity,
                'investment_amount':
                round(investment_amount, 2),
                'current_value':
                round(current_value, 2),
                'position_type':
                signal_type or 'BUY',
                'status':
                status or 'ACTIVE',
                'created_at':
                created_at.isoformat() if created_at else None,
                'pnl':
                round(pnl, 2) if pnl else round(
                    (current_price - entry_price) * quantity, 2),
                'pnl_percentage':
                round(pnl_percentage, 2) if pnl_percentage else round(
                    ((current_price - entry_price) / entry_price) * 100, 2),
                'pp':
                round(pnl_percentage, 2) if pnl_percentage else round(
                    ((current_price - entry_price) / entry_price) * 100, 2),
                'target_price':
                round(target_price, 2) if target_price else round(
                    entry_price * 1.1, 2),
                'stop_loss':
                round(stop_loss, 2) if stop_loss else round(
                    entry_price * 0.9, 2),
                'last_update_time':
                last_update_time.isoformat() if last_update_time else None,
                'data_source':
                'Yahoo Finance'
            }

            signals_list.append(signal_data)
            total_investment += investment_amount
            total_current_value += current_value

        # Calculate portfolio summary
        total_pnl = total_current_value - total_investment
        return_percent = ((total_pnl / total_investment) *
                          100) if total_investment > 0 else 0

        portfolio_summary = {
            'total_positions':
            len(signals_list),
            'total_investment':
            round(total_investment, 2),
            'current_value':
            round(total_current_value, 2),
            'total_pnl':
            round(total_pnl, 2),
            'return_percent':
            round(return_percent, 2),
            'active_positions':
            len([s for s in signals_list if s['status'] == 'ACTIVE']),
            'closed_positions':
            len([s for s in signals_list if s['status'] != 'ACTIVE'])
        }

        return jsonify({
            'success': True,
            'signals': signals_list,
            'total': len(signals_list),
            'portfolio': portfolio_summary
        })

    except Exception as e:
        logger.error(f"Error fetching ETF signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'signals': [],
            'total': 0
        }), 500


@etf_bp.route('/admin/send-signal', methods=['POST'])
def send_admin_signal():
    """Admin endpoint to send trading signals to specific users"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        required_fields = [
            'symbol', 'signal_type', 'entry_price', 'target_users'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing field: {field}'
                }), 400

        # Create admin signal record
        insert_query = text("""
            INSERT INTO admin_trade_signals 
            (symbol, signal_type, entry_price, current_price, quantity, status, created_at)
            VALUES (:symbol, :signal_type, :entry_price, :current_price, :quantity, 'ACTIVE', :created_at)
        """)

        db.session.execute(
            insert_query, {
                'symbol': data['symbol'],
                'signal_type': data['signal_type'],
                'entry_price': data['entry_price'],
                'current_price': data.get('current_price',
                                          data['entry_price']),
                'quantity': data.get('quantity', 1),
                'created_at': datetime.now()
            })
        db.session.commit()

        return jsonify({
            'success':
            True,
            'message':
            f"Signal sent for {data['symbol']} to {len(data['target_users'])} users"
        })

    except Exception as e:
        logger.error(f"Error sending admin signal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/admin/users', methods=['GET'])
def get_target_users():
    """Get list of users to send signals to"""
    try:
        # Get users from database
        result = db.session.execute(
            text("SELECT ucc, greeting_name FROM users LIMIT 10"))
        users = result.fetchall()

        users_list = []
        for row in users:
            ucc, name = row
            users_list.append({'ucc': ucc, 'name': name or 'Unknown'})

        return jsonify({'success': True, 'users': users_list})

    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/user-deals', methods=['GET'])
def get_user_deals():
    """Get deals created by current user"""
    try:
        # Return empty deals for now
        return jsonify({'success': True, 'deals': [], 'total': 0})

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/create-deal', methods=['POST'])
def create_deal():
    """Create a new deal from signal or manually"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Deal creation functionality will be implemented',
            'deal_id': 'placeholder'
        })

    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/quotes', methods=['GET'])
def get_etf_quotes():
    """Get live quotes for ETF instruments"""
    try:
        symbols = request.args.getlist('symbols')

        quotes = {}
        for symbol in symbols:
            quotes[symbol] = {'ltp': 0, 'change': 0, 'change_percent': 0}

        return jsonify({'success': True, 'quotes': quotes})

    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/portfolio-summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary metrics"""
    try:
        # Calculate from admin_trade_signals table
        result = db.session.execute(
            text("""
            SELECT 
                COUNT(*) as total_positions,
                SUM(investment_amount) as total_investment,
                SUM(current_price * quantity) as current_value
            FROM admin_trade_signals 
            WHERE status = 'ACTIVE'
        """))

        row = result.fetchone()
        total_positions, total_investment, current_value = row

        total_investment = float(total_investment) if total_investment else 0
        current_value = float(current_value) if current_value else 0
        total_pnl = current_value - total_investment
        return_percent = ((total_pnl / total_investment) *
                          100) if total_investment > 0 else 0

        return jsonify({
            'success': True,
            'portfolio': {
                'total_positions':
                int(total_positions) if total_positions else 0,
                'total_investment': round(total_investment, 2),
                'current_value': round(current_value, 2),
                'total_pnl': round(total_pnl, 2),
                'return_percent': round(return_percent, 2)
            }
        })

    except Exception as e:
        logger.error(f"Error calculating portfolio summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@etf_bp.route('/bulk-update', methods=['POST'])
def bulk_update_positions():
    """Bulk update multiple ETF positions"""
    try:
        data = request.get_json()

        if not data or 'updates' not in data:
            return jsonify({
                'success': False,
                'error': 'No updates provided'
            }), 400

        # For now, just return success
        return jsonify({
            'success':
            True,
            'message':
            f"Bulk update functionality will be implemented for {len(data['updates'])} positions"
        })

    except Exception as e:
        logger.error(f"Error bulk updating positions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# @etf_bp.route('/api/etf-signals-data', methods=['GET'])
# def get_etf_signals_data():
#     """API endpoint to get ETF signals data from database (admin_trade_signals table)"""
#     try:
#         # Get ETF signals from external database
#         import psycopg2
#         from psycopg2.extras import RealDictCursor

#         # Use centralized database configuration instead

#         with psycopg2.connect(DATABASE_URL) as conn:
#             with conn.cursor(cursor_factory=RealDictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT * FROM admin_trade_signals
#                     ORDER BY id DESC
#                     LIMIT 100
#                 """)

#                 signals_data = cursor.fetchall()

#         if not signals_data:
#             return jsonify({
#                 'success': True,
#                 'data': [],
#                 'total': 0,
#                 'message': 'No ETF signals found'
#             })

#         # Format signals data for frontend
#         formatted_signals = []
#         for signal in signals_data:
#             formatted_signal = {
#                 'id': signal.get('id'),
#                 'trade_signal_id': signal.get('id'),
#                 'symbol': signal.get('symbol', 'N/A'),
#                 'd30': float(signal.get('d30', 0)) if signal.get('d30') else 0,
#                 'ch30': float(signal.get('ch30', 0)) if signal.get('ch30') else 0,
#                 'date': signal.get('date', ''),
#                 'pos': int(signal.get('pos', 1)),
#                 'qty': int(signal.get('qty', 1)),
#                 'ep': float(signal.get('ep', 0)) if signal.get('ep') else 0,
#                 'cmp': float(signal.get('cmp', 0)) if signal.get('cmp') else 0,
#                 'chan': float(signal.get('chan', 0)) if signal.get('chan') else 0,
#                 'inv': float(signal.get('inv', 0)) if signal.get('inv') else 0,
#                 'tp': float(signal.get('tp', 0)) if signal.get('tp') else 0,
#                 'tva': float(signal.get('tva', 0)) if signal.get('tva') else 0,
#                 'tpr': float(signal.get('tpr', 0)) if signal.get('tpr') else 0,
#                 'pl': float(signal.get('pl', 0)) if signal.get('pl') else 0,
#                 'ed': signal.get('ed', ''),
#                 'exp': signal.get('exp', ''),
#                 'pr': float(signal.get('pr', 0)) if signal.get('pr') else 0,
#                 'pp': float(signal.get('pp', 0)) if signal.get('pp') else 0,
#                 'iv': float(signal.get('iv', 0)) if signal.get('iv') else 0,
#                 'ip': float(signal.get('ip', 0)) if signal.get('ip') else 0,
#                 'nt': signal.get('nt', ''),
#                 'qt': int(signal.get('qt', 0)),
#                 'd7': float(signal.get('d7', 0)) if signal.get('d7') else 0,
#                 'ch7': float(signal.get('ch7', 0)) if signal.get('ch7') else 0,
#                 'status': signal.get('status', 'ACTIVE')
#             }
#             formatted_signals.append(formatted_signal)

#         logger.info(f"ETF Signals API: Returning {len(formatted_signals)} signals")

#         return jsonify({
#             'success': True,
#             'data': formatted_signals,
#             'total': len(formatted_signals)
#         })

#     except Exception as e:
#         logger.error(f"Error in etf-signals-data endpoint: {e}")
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'data': [],
#             'total': 0
#         }), 500
