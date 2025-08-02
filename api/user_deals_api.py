
"""
User Deals API - Clean API for user deals management
Handles CRUD operations for user deals with proper error handling
"""
from flask import Blueprint, request, jsonify, session
from Scripts.models import db, User
from Scripts.models_etf import UserDeal
from datetime import datetime
import logging
from functools import wraps

user_deals_bp = Blueprint('user_deals', __name__, url_prefix='/api')

def get_current_user_id():
    """Get current user ID from session"""
    user_ucc = session.get('ucc')
    user_id = session.get('user_id') or session.get('db_user_id')

    if user_ucc:
        user = User.query.filter_by(ucc=user_ucc).first()
        if user:
            return user.id
        else:
            # Create user if doesn't exist
            try:
                new_user = User(
                    ucc=user_ucc,
                    mobile_number=session.get('mobile_number', ''),
                    greeting_name=session.get('greeting_name', str(user_ucc)),
                    user_id=str(user_ucc),
                    is_active=True
                )
                db.session.add(new_user)
                db.session.commit()
                return new_user.id
            except Exception as e:
                logging.error(f"Error creating user: {e}")
                db.session.rollback()
                return None

    if user_id:
        user = User.query.get(user_id)
        if user:
            return user.id

    # Return None for unauthenticated users
    return None

@user_deals_bp.route('/deals', methods=['GET'])
def get_user_deals():
    """Get all deals for current user from user_deals table"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User not authenticated',
                'deals': []
            }), 401

        # Get query parameters for filtering and pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        symbol_filter = request.args.get('symbol')
        status_filter = request.args.get('status')
        deal_type_filter = request.args.get('deal_type')

        # Build query
        query = UserDeal.query.filter_by(user_id=user_id)

        # Apply filters
        if symbol_filter:
            query = query.filter(UserDeal.symbol.ilike(f'%{symbol_filter}%'))

        if status_filter:
            query = query.filter(UserDeal.status == status_filter.upper())

        if deal_type_filter:
            query = query.filter(UserDeal.deal_type == deal_type_filter.upper())

        # Get total count before pagination
        total_deals = query.count()

        # Apply pagination and ordering
        deals = query.order_by(UserDeal.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Convert to dict format
        deals_data = []
        for deal in deals.items:
            try:
                deal_dict = deal.to_dict()
                deals_data.append(deal_dict)
            except Exception as e:
                logging.error(f"Error converting deal {deal.id} to dict: {e}")
                continue

        return jsonify({
            'success': True,
            'deals': deals_data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_deals': total_deals,
                'total_pages': deals.pages,
                'has_next': deals.has_next,
                'has_prev': deals.has_prev
            },
            'user_id': user_id
        })

    except Exception as e:
        logging.error(f"Error fetching user deals: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching deals: {str(e)}',
            'deals': []
        }), 500

@user_deals_bp.route('/deals', methods=['POST'])
def create_user_deal():
    """Create a new deal in user_deals table"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        data = request.get_json()

        # Validate required fields
        required_fields = ['symbol', 'position_type', 'quantity', 'entry_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Helper functions for safe conversion
        def safe_float(value, default=0.0):
            try:
                if value is None or value == '':
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                if value is None or value == '':
                    return default
                return int(float(value))
            except (ValueError, TypeError):
                return default

        # Extract and validate data
        symbol = str(data['symbol']).upper()
        position_type = str(data['position_type']).upper()
        quantity = safe_int(data['quantity'])
        entry_price = safe_float(data['entry_price'])

        if quantity <= 0 or entry_price <= 0:
            return jsonify({'success': False, 'message': 'Quantity and entry price must be positive'}), 400

        # Calculate invested amount
        invested_amount = quantity * entry_price

        # Create new deal
        deal = UserDeal(
            user_id=user_id,
            symbol=symbol,
            trading_symbol=data.get('trading_symbol', symbol),
            exchange=data.get('exchange', 'NSE'),
            position_type=position_type,
            quantity=quantity,
            entry_price=entry_price,
            current_price=safe_float(data.get('current_price', entry_price)),
            target_price=safe_float(data.get('target_price')) if data.get('target_price') else None,
            stop_loss=safe_float(data.get('stop_loss')) if data.get('stop_loss') else None,
            invested_amount=invested_amount,
            notes=data.get('notes', ''),
            tags=data.get('tags', ''),
            deal_type=data.get('deal_type', 'MANUAL'),
            status='ACTIVE'
        )

        # Calculate P&L
        try:
            deal.calculate_pnl()
        except Exception as calc_error:
            logging.warning(f"Could not calculate P&L for new deal: {calc_error}")
            deal.pnl_amount = 0.0
            deal.pnl_percent = 0.0

        db.session.add(deal)
        db.session.commit()

        logging.info(f"Deal created for user {user_id}: {deal.symbol} {deal.position_type}")

        return jsonify({
            'success': True,
            'message': 'Deal created successfully',
            'deal': deal.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating deal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating deal: {str(e)}'}), 500

@user_deals_bp.route('/deals/<int:deal_id>', methods=['PUT'])
def update_user_deal(deal_id):
    """Update existing deal"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()

        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'current_price' in data:
            deal.current_price = float(data['current_price'])

        if 'target_price' in data:
            deal.target_price = float(data['target_price']) if data['target_price'] else None

        if 'stop_loss' in data:
            deal.stop_loss = float(data['stop_loss']) if data['stop_loss'] else None

        if 'notes' in data:
            deal.notes = data['notes']

        if 'tags' in data:
            deal.tags = data['tags']

        if 'status' in data:
            deal.status = data['status'].upper()

        deal.updated_at = datetime.utcnow()

        # Recalculate P&L
        try:
            deal.calculate_pnl()
        except Exception as calc_error:
            logging.warning(f"Could not calculate P&L for deal: {calc_error}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Deal updated successfully',
            'deal': deal.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating deal {deal_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating deal: {str(e)}'}), 500

@user_deals_bp.route('/deals/<int:deal_id>', methods=['DELETE'])
def delete_user_deal(deal_id):
    """Delete a deal"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()

        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404

        db.session.delete(deal)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Deal deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting deal {deal_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting deal: {str(e)}'}), 500

@user_deals_bp.route('/deals/stats', methods=['GET'])
def get_user_deals_stats():
    """Get deals statistics for current user"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get all deals for user
        deals = UserDeal.query.filter_by(user_id=user_id).all()

        # Calculate statistics
        stats = {
            'total_deals': len(deals),
            'active_deals': len([d for d in deals if d.status == 'ACTIVE']),
            'closed_deals': len([d for d in deals if d.status == 'CLOSED']),
            'total_invested': sum([float(d.invested_amount or 0) for d in deals]),
            'total_pnl': sum([float(d.pnl_amount or 0) for d in deals]),
            'winning_deals': len([d for d in deals if (d.pnl_amount or 0) > 0]),
            'losing_deals': len([d for d in deals if (d.pnl_amount or 0) < 0]),
            'long_positions': len([d for d in deals if d.position_type == 'LONG']),
            'short_positions': len([d for d in deals if d.position_type == 'SHORT'])
        }

        # Calculate success rate
        stats['success_rate'] = (stats['winning_deals'] / stats['total_deals']) * 100 if stats['total_deals'] > 0 else 0

        # Calculate average P&L
        stats['avg_pnl'] = stats['total_pnl'] / stats['total_deals'] if stats['total_deals'] > 0 else 0

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logging.error(f"Error fetching deals stats: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching stats: {str(e)}'}), 500

@user_deals_bp.route('/user-deals-data', methods=['GET'])
def get_user_deals_data():
    """Get user deals data in the format expected by the frontend deals.js"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User not logged in or authenticated',
                'deals': []
            }), 401

        # Get query parameters for filtering and pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        symbol_filter = request.args.get('symbol')
        status_filter = request.args.get('status')

        # Build query
        query = UserDeal.query.filter_by(user_id=user_id)

        # Apply filters
        if symbol_filter:
            query = query.filter(UserDeal.symbol.ilike(f'%{symbol_filter}%'))

        if status_filter:
            query = query.filter(UserDeal.status == status_filter.upper())

        # Get total count
        total_deals = query.count()

        # Apply ordering and pagination
        deals = query.order_by(UserDeal.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Format deals data for frontend
        formatted_deals = []
        for deal in deals.items:
            try:
                # Format the deal data to match what the frontend expects
                formatted_deal = {
                    'id': deal.id,
                    'trade_signal_id': deal.trade_signal_id or str(deal.id),
                    'symbol': deal.symbol,
                    'trading_symbol': deal.trading_symbol,
                    'etf_symbol': deal.etf_symbol,
                    'exchange': deal.exchange,
                    
                    # Position and quantity
                    'pos': deal.pos or (1 if deal.position_type == 'LONG' else -1),
                    'position_type': deal.position_type,
                    'qty': deal.qty or deal.quantity,
                    'quantity': deal.quantity,
                    
                    # Prices
                    'ep': float(deal.ep or deal.entry_price or 0),
                    'entry_price': float(deal.entry_price or 0),
                    'cmp': float(deal.cmp or deal.current_price or deal.entry_price or 0),
                    'current_price': float(deal.current_price or 0),
                    'tp': float(deal.tp or deal.target_price or 0),
                    'target_price': float(deal.target_price or 0),
                    'stop_loss': float(deal.stop_loss or 0),
                    
                    # Investment and P&L
                    'inv': float(deal.inv or deal.invested_amount or 0),
                    'invested_amount': float(deal.invested_amount or 0),
                    'current_value': float(deal.current_value or 0),
                    'pl': float(deal.pl or deal.pnl_amount or 0),
                    'pnl_amount': float(deal.pnl_amount or 0),
                    'pnl_percent': float(deal.pnl_percent or 0),
                    
                    # Performance data
                    'chan_percent': deal.chan_percent or f"{float(deal.pnl_percent or 0):.2f}%",
                    'thirty': deal.thirty,
                    'seven': deal.seven,
                    'ch': deal.ch,
                    
                    # Target calculations
                    'tpr': float(deal.tpr or 0),
                    'tva': float(deal.tva or 0),
                    
                    # Dates and metadata
                    'signal_date': deal.signal_date,
                    'ed': deal.ed,
                    'exp': deal.exp,
                    'date': deal.signal_date or deal.ed,
                    'dh': deal.dh or 0,
                    'qt': deal.qt,
                    
                    # Additional fields
                    'pr': deal.pr,
                    'pp': deal.pp,
                    'iv': deal.iv,
                    'ip': deal.ip,
                    'nt': deal.nt,
                    'notes': deal.notes,
                    'tags': deal.tags,
                    
                    # Status and timestamps
                    'status': deal.status,
                    'deal_type': deal.deal_type,
                    'created_at': deal.created_at.isoformat() if deal.created_at else None,
                    'updated_at': deal.updated_at.isoformat() if deal.updated_at else None
                }
                formatted_deals.append(formatted_deal)
            except Exception as e:
                logging.error(f"Error formatting deal {deal.id}: {e}")
                continue

        # Return in the format expected by frontend
        return jsonify({
            'success': True,
            'deals': formatted_deals,
            'data': formatted_deals,  # Alternative key the frontend might check
            'recordsTotal': total_deals,
            'recordsFiltered': total_deals,
            'total': total_deals,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_deals': total_deals,
                'total_pages': deals.pages,
                'has_next': deals.has_next,
                'has_prev': deals.has_prev
            },
            'user_id': user_id
        })

    except Exception as e:
        logging.error(f"Error fetching user-deals-data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching user deals data: {str(e)}',
            'deals': []
        }), 500
