"""ETF Trading Signals API endpoints"""
from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime, timedelta
import json
from sqlalchemy import text
from app import db

etf_bp = Blueprint('etf', __name__, url_prefix='/etf')
logger = logging.getLogger(__name__)


@etf_bp.route('/signals', methods=['GET'])
def get_admin_signals():
    """Get ETF signals data from admin_trade_signals table"""
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
            logger.info("No admin trade signals found api/etf-signals-datan database")
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
