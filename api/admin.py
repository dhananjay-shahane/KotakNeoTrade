"""
Admin API endpoints for trade signal management
"""
from flask import Blueprint, request, jsonify, session
from scripts.models import db, User
from scripts.models_etf import AdminTradeSignal, UserNotification, UserDeal, ETFSignalTrade
from datetime import datetime, timedelta
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/send-signal', methods=['POST'])
def send_trade_signal():
    """Send trade signal to specific user"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Get admin user
        admin_user = User.query.get(session['user_id'])
        if not admin_user:
            return jsonify({'success': False, 'message': 'Admin user not found'}), 404
        
        # For now, allow all users to send signals (you can add admin role check here)
        # if not admin_user.is_admin:  # Add this field to User model if needed
        #     return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['target_user_id', 'symbol', 'signal_type', 'entry_price', 'quantity', 'signal_title']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if target user exists
        target_user = User.query.get(data['target_user_id'])
        if not target_user:
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Create trade signal
        signal = AdminTradeSignal(
            admin_user_id=admin_user.id,
            target_user_id=data['target_user_id'],
            symbol=data['symbol'].upper(),
            trading_symbol=data['symbol'].upper(),  # Simplified for now
            token=f"TOKEN_{data['symbol'].upper()}",  # Simplified for now
            exchange=data.get('exchange', 'NSE'),
            signal_type=data['signal_type'].upper(),
            entry_price=float(data['entry_price']),
            target_price=float(data['target_price']) if data.get('target_price') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            quantity=int(data['quantity']),
            signal_title=data['signal_title'],
            signal_description=data.get('signal_description'),
            priority=data.get('priority', 'MEDIUM').upper(),
            expires_at=datetime.utcnow() + timedelta(days=7)  # Signal expires in 7 days
        )
        
        db.session.add(signal)
        db.session.flush()  # Get the signal ID
        
        # Create notification for target user
        notification = UserNotification(
            user_id=data['target_user_id'],
            title=f"New Trade Signal: {data['signal_title']}",
            message=f"{data['signal_type']} {data['symbol']} @ ₹{data['entry_price']} - {data.get('signal_description', 'No description')}",
            notification_type='TRADE_SIGNAL',
            priority=data.get('priority', 'MEDIUM').upper(),
            related_signal_id=signal.id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"Trade signal sent from user {admin_user.id} to user {data['target_user_id']}: {data['signal_title']}")
        
        return jsonify({
            'success': True,
            'message': 'Trade signal sent successfully',
            'signal_id': signal.id
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending trade signal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending signal: {str(e)}'}), 500

@admin_bp.route('/signals', methods=['GET'])
def get_sent_signals():
    """Get all signals sent by current admin"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        signals = AdminTradeSignal.query.filter_by(admin_user_id=session['user_id']).order_by(AdminTradeSignal.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'signals': [signal.to_dict() for signal in signals]
        })
        
    except Exception as e:
        logging.error(f"Error fetching sent signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching signals: {str(e)}'}), 500

@admin_bp.route('/users', methods=['GET'])
def get_users_list():
    """Get list of users for admin to send signals to"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        users = User.query.filter(User.id != session['user_id']).all()
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'ucc': user.ucc,
                'greeting_name': user.greeting_name,
                'mobile_number': user.mobile_number
            } for user in users]
        })
        
    except Exception as e:
        logging.error(f"Error fetching users list: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching users: {str(e)}'}), 500

@admin_bp.route('/bulk-signal', methods=['POST'])
def send_bulk_trade_signals():
    """Send trade signals to multiple users from uploaded CSV/data"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        admin_user = User.query.get(session['user_id'])
        if not admin_user:
            return jsonify({'success': False, 'message': 'Admin user not found'}), 404
        
        data = request.get_json()
        signals_data = data.get('signals', [])
        target_user_ids = data.get('target_user_ids', [])
        
        if not signals_data:
            return jsonify({'success': False, 'message': 'No signals data provided'}), 400
        
        if not target_user_ids:
            return jsonify({'success': False, 'message': 'No target users specified'}), 400
        
        created_signals = []
        created_notifications = []
        
        for signal_data in signals_data:
            for user_id in target_user_ids:
                # Create trade signal
                signal = AdminTradeSignal(
                    admin_user_id=admin_user.id,
                    target_user_id=user_id,
                    symbol=signal_data.get('symbol', '').upper(),
                    trading_symbol=signal_data.get('symbol', '').upper(),
                    token=f"TOKEN_{signal_data.get('symbol', '').upper()}",
                    exchange=signal_data.get('exchange', 'NSE'),
                    signal_type=signal_data.get('signal_type', 'BUY').upper(),
                    entry_price=float(signal_data.get('entry_price', 0)),
                    target_price=float(signal_data.get('target_price')) if signal_data.get('target_price') else None,
                    stop_loss=float(signal_data.get('stop_loss')) if signal_data.get('stop_loss') else None,
                    quantity=int(signal_data.get('quantity', 1)),
                    signal_title=signal_data.get('signal_title', f"{signal_data.get('signal_type', 'BUY')} {signal_data.get('symbol', '')}"),
                    signal_description=signal_data.get('signal_description', ''),
                    priority=signal_data.get('priority', 'MEDIUM').upper(),
                    current_price=float(signal_data.get('current_price')) if signal_data.get('current_price') else None,
                    change_percent=float(signal_data.get('change_percent')) if signal_data.get('change_percent') else None,
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                
                db.session.add(signal)
                db.session.flush()
                created_signals.append(signal)
                
                # Create notification
                notification = UserNotification(
                    user_id=user_id,
                    title=f"New Trade Signal: {signal.signal_title}",
                    message=f"{signal.signal_type} {signal.symbol} @ ₹{signal.entry_price} - {signal.signal_description or 'No description'}",
                    notification_type='TRADE_SIGNAL',
                    priority=signal.priority,
                    related_signal_id=signal.id
                )
                
                db.session.add(notification)
                created_notifications.append(notification)
        
        db.session.commit()
        
        logging.info(f"Bulk signals sent: {len(created_signals)} signals to {len(target_user_ids)} users")
        
        return jsonify({
            'success': True,
            'message': f'Successfully sent {len(created_signals)} signals to {len(target_user_ids)} users',
            'signals_created': len(created_signals),
            'notifications_created': len(created_notifications)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending bulk signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending bulk signals: {str(e)}'}), 500

@admin_bp.route('/deals', methods=['GET'])
def get_all_deals():
    """Get all deals across all users (admin view)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Get all deals with user information
        deals = db.session.query(UserDeal, User).join(User, UserDeal.user_id == User.id).all()
        
        deals_data = []
        for deal, user in deals:
            deal_dict = deal.to_dict()
            deal_dict['user_info'] = {
                'ucc': user.ucc,
                'greeting_name': user.greeting_name,
                'mobile_number': user.mobile_number
            }
            deals_data.append(deal_dict)
        
        return jsonify({
            'success': True,
            'deals': deals_data,
            'total_deals': len(deals_data)
        })
        
    except Exception as e:
        logging.error(f"Error fetching all deals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching deals: {str(e)}'}), 500

@admin_bp.route('/deal/<int:deal_id>', methods=['PUT'])
def update_deal():
    """Update a specific deal"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        deal = UserDeal.query.get(deal_id)
        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404
        
        data = request.get_json()
        
        # Update deal fields
        if 'current_price' in data:
            deal.current_price = float(data['current_price'])
            deal.last_price_update = datetime.utcnow()
            deal.calculate_pnl()
        
        if 'status' in data:
            deal.status = data['status'].upper()
            if deal.status == 'CLOSED':
                deal.exit_date = datetime.utcnow()
        
        if 'notes' in data:
            deal.notes = data['notes']
        
        deal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deal updated successfully',
            'deal': deal.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating deal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating deal: {str(e)}'}), 500

@admin_bp.route('/etf-signal-trades', methods=['GET'])
def get_all_etf_signal_trades():
    """Get all ETF signal trades across all users (admin view)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Get all ETF signal trades with user information
        trades = db.session.query(ETFSignalTrade, User).join(User, ETFSignalTrade.user_id == User.id).all()
        
        trades_data = []
        for trade, user in trades:
            trade_dict = trade.to_dict()
            trade_dict['user_info'] = {
                'ucc': user.ucc,
                'greeting_name': user.greeting_name,
                'mobile_number': user.mobile_number
            }
            trades_data.append(trade_dict)
        
        return jsonify({
            'success': True,
            'trades': trades_data,
            'total_trades': len(trades_data)
        })
        
    except Exception as e:
        logging.error(f"Error fetching all ETF signal trades: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching trades: {str(e)}'}), 500

@admin_bp.route('/assign-etf-signal', methods=['POST'])
def assign_etf_signal_trade():
    """Assign ETF signal trade to specific user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        admin_user = User.query.get(session['user_id'])
        if not admin_user:
            return jsonify({'success': False, 'message': 'Admin user not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['target_user_id', 'symbol', 'signal_type', 'entry_price', 'quantity', 'trade_title']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if target user exists
        target_user = User.query.get(data['target_user_id'])
        if not target_user:
            return jsonify({'success': False, 'message': 'Target user not found'}), 404
        
        # Calculate invested amount
        invested_amount = float(data['entry_price']) * int(data['quantity'])
        
        # Create ETF signal trade
        trade = ETFSignalTrade(
            user_id=data['target_user_id'],
            assigned_by_user_id=admin_user.id,
            symbol=data['symbol'].upper(),
            etf_name=data.get('etf_name'),
            trading_symbol=data.get('trading_symbol', f"{data['symbol'].upper()}-EQ"),
            token=data.get('token', f"TOKEN_{data['symbol'].upper()}"),
            exchange=data.get('exchange', 'NSE'),
            signal_type=data['signal_type'].upper(),
            quantity=int(data['quantity']),
            entry_price=float(data['entry_price']),
            current_price=float(data.get('current_price', data['entry_price'])),
            target_price=float(data['target_price']) if data.get('target_price') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            invested_amount=invested_amount,
            current_value=invested_amount,
            trade_title=data['trade_title'],
            trade_description=data.get('trade_description'),
            priority=data.get('priority', 'MEDIUM').upper(),
            position_type=data.get('position_type', 'LONG').upper(),
            change_pct=data.get('change_pct', '0.00%'),
            tp_value=float(data['tp_value']) if data.get('tp_value') else None,
            tp_return=data.get('tp_return')
        )
        
        # Calculate initial P&L
        trade.calculate_pnl()
        
        db.session.add(trade)
        db.session.flush()
        
        # Create notification for target user
        notification = UserNotification(
            user_id=data['target_user_id'],
            title=f"New ETF Signal: {data['trade_title']}",
            message=f"{data['signal_type']} {data['symbol']} @ ₹{data['entry_price']} - {data.get('trade_description', 'No description')}",
            notification_type='TRADE_SIGNAL',
            priority=data.get('priority', 'MEDIUM').upper()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"ETF signal trade assigned from user {admin_user.id} to user {data['target_user_id']}: {data['trade_title']}")
        
        return jsonify({
            'success': True,
            'message': 'ETF signal trade assigned successfully',
            'trade_id': trade.id
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error assigning ETF signal trade: {str(e)}")
        return jsonify({'success': False, 'message': f'Error assigning trade: {str(e)}'}), 500

@admin_bp.route('/bulk-assign-etf-signals', methods=['POST'])
def bulk_assign_etf_signals():
    """Bulk assign ETF signal trades to multiple users"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        admin_user = User.query.get(session['user_id'])
        if not admin_user:
            return jsonify({'success': False, 'message': 'Admin user not found'}), 404
        
        data = request.get_json()
        trades_data = data.get('trades', [])
        target_user_ids = data.get('target_user_ids', [])
        
        if not trades_data:
            return jsonify({'success': False, 'message': 'No trades data provided'}), 400
        
        if not target_user_ids:
            return jsonify({'success': False, 'message': 'No target users specified'}), 400
        
        created_trades = []
        created_notifications = []
        
        for trade_data in trades_data:
            for user_id in target_user_ids:
                # Calculate invested amount
                invested_amount = float(trade_data.get('entry_price', 0)) * int(trade_data.get('quantity', 1))
                
                # Create ETF signal trade
                trade = ETFSignalTrade(
                    user_id=user_id,
                    assigned_by_user_id=admin_user.id,
                    symbol=trade_data.get('symbol', '').upper(),
                    etf_name=trade_data.get('etf_name'),
                    trading_symbol=trade_data.get('trading_symbol', f"{trade_data.get('symbol', '').upper()}-EQ"),
                    token=trade_data.get('token', f"TOKEN_{trade_data.get('symbol', '').upper()}"),
                    exchange=trade_data.get('exchange', 'NSE'),
                    signal_type=trade_data.get('signal_type', 'BUY').upper(),
                    quantity=int(trade_data.get('quantity', 1)),
                    entry_price=float(trade_data.get('entry_price', 0)),
                    current_price=float(trade_data.get('current_price', trade_data.get('entry_price', 0))),
                    target_price=float(trade_data.get('target_price')) if trade_data.get('target_price') else None,
                    stop_loss=float(trade_data.get('stop_loss')) if trade_data.get('stop_loss') else None,
                    invested_amount=invested_amount,
                    current_value=invested_amount,
                    trade_title=trade_data.get('trade_title', f"{trade_data.get('signal_type', 'BUY')} {trade_data.get('symbol', '')}"),
                    trade_description=trade_data.get('trade_description', ''),
                    priority=trade_data.get('priority', 'MEDIUM').upper(),
                    position_type=trade_data.get('position_type', 'LONG').upper(),
                    change_pct=trade_data.get('change_pct', '0.00%'),
                    tp_value=float(trade_data.get('tp_value')) if trade_data.get('tp_value') else None,
                    tp_return=trade_data.get('tp_return')
                )
                
                # Calculate initial P&L
                trade.calculate_pnl()
                
                db.session.add(trade)
                db.session.flush()
                created_trades.append(trade)
                
                # Create notification
                notification = UserNotification(
                    user_id=user_id,
                    title=f"New ETF Signal: {trade.trade_title}",
                    message=f"{trade.signal_type} {trade.symbol} @ ₹{trade.entry_price} - {trade.trade_description or 'No description'}",
                    notification_type='TRADE_SIGNAL',
                    priority=trade.priority
                )
                
                db.session.add(notification)
                created_notifications.append(notification)
        
        db.session.commit()
        
        logging.info(f"Bulk ETF signals assigned: {len(created_trades)} trades to {len(target_user_ids)} users")
        
        return jsonify({
            'success': True,
            'message': f'Successfully assigned {len(created_trades)} ETF signal trades to {len(target_user_ids)} users',
            'trades_created': len(created_trades),
            'notifications_created': len(created_notifications)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk assigning ETF signals: {str(e)}")
        return jsonify({'success': False, 'message': f'Error bulk assigning trades: {str(e)}'}), 500