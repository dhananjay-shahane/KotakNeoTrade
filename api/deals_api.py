
from flask import Blueprint, jsonify, request
from Scripts.models import db, UserDeals
from datetime import datetime
import logging

deals_api = Blueprint('deals_api', __name__)

@deals_api.route('/api/user-deals-data', methods=['GET'])
def get_user_deals_data():
    try:
        # Query all deals including closed ones, ordered by status (active first)
        deals = UserDeals.query.order_by(
            UserDeals.status.asc(),  # ACTIVE comes before CLOSED
            UserDeals.entry_date.desc()
        ).all()
        
        deals_data = []
        for deal in deals:
            deal_dict = {
                'id': deal.id,
                'trade_signal_id': deal.id,
                'symbol': deal.symbol,
                'quantity': deal.quantity,
                'entry_price': float(deal.entry_price) if deal.entry_price else 0,
                'current_price': float(deal.current_price) if deal.current_price else float(deal.entry_price) if deal.entry_price else 0,
                'invested_amount': float(deal.invested_amount) if deal.invested_amount else 0,
                'pnl_amount': float(deal.pnl_amount) if deal.pnl_amount else 0,
                'pnl_percent': float(deal.pnl_percent) if deal.pnl_percent else 0,
                'status': deal.status or 'ACTIVE',
                'entry_date': deal.entry_date.strftime('%Y-%m-%d') if deal.entry_date else '',
                'exit_date': deal.exit_date.strftime('%Y-%m-%d') if deal.exit_date else None,
                'deal_type': deal.deal_type or 'MANUAL',
                'exchange': deal.exchange or 'NSE',
                'trading_symbol': deal.symbol,
                'chan_percent': float(deal.pnl_percent) if deal.pnl_percent else 0,
                'tp': 0,
                'tva': 0,
                'tpr': '15.00%',
                'seven': '--',
                'seven_percent': '--',
                'thirty': '--',
                'thirty_percent': '--',
                'qt': 1,
                'ed': deal.exit_date.strftime('%d/%m/%Y') if deal.exit_date else '--',
                'exp': '--',
                'pr': '--',
                'pp': '--',
                'iv': '--',
                'ip': '--'
            }
            deals_data.append(deal_dict)
        
        return jsonify({
            'success': True,
            'data': deals_data,
            'total': len(deals_data)
        })
        
    except Exception as e:
        logging.error(f"Error fetching user deals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@deals_api.route('/api/close-deal', methods=['POST'])
def close_deal():
    try:
        data = request.get_json()
        deal_id = data.get('deal_id')
        symbol = data.get('symbol')
        
        if not deal_id:
            return jsonify({'success': False, 'message': 'Deal ID is required'}), 400
        
        # Find the deal
        deal = UserDeals.query.get(deal_id)
        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404
        
        # Update deal status to CLOSED and set exit date
        deal.status = 'CLOSED'
        deal.exit_date = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deal closed successfully for {symbol}',
            'deal_id': deal_id
        })
        
    except Exception as e:
        logging.error(f"Error closing deal: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@deals_api.route('/api/edit-deal', methods=['POST'])
def edit_deal():
    try:
        data = request.get_json()
        deal_id = data.get('deal_id')
        entry_price = data.get('entry_price')
        target_price = data.get('target_price')
        
        if not deal_id:
            return jsonify({'success': False, 'message': 'Deal ID is required'}), 400
        
        # Find the deal
        deal = UserDeals.query.get(deal_id)
        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404
        
        # Don't allow editing closed deals
        if deal.status == 'CLOSED':
            return jsonify({'success': False, 'message': 'Cannot edit closed deals'}), 400
        
        # Update deal
        if entry_price:
            deal.entry_price = float(entry_price)
            # Recalculate invested amount
            deal.invested_amount = deal.quantity * float(entry_price)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Deal updated successfully',
            'deal_id': deal_id
        })
        
    except Exception as e:
        logging.error(f"Error editing deal: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
