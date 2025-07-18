"""
Clean Deals API - Focused on user_deals table operations
Provides CRUD operations for user deals with proper error handling
"""
from flask import Blueprint, request, jsonify, session
from Scripts.models import db, User
from Scripts.models_etf import UserDeal
import json
from datetime import datetime
import logging
from functools import wraps

deals_bp = Blueprint('deals', __name__, url_prefix='/api/deals')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    """Get current user ID from session or create default user"""
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

    # Default user for testing
    return 1

@deals_bp.route('/', methods=['GET'])
def get_deals():
    """Get all deals for current user from user_deals table"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User not found',
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
        logging.error(f"Error fetching deals: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching deals: {str(e)}',
            'deals': []
        }), 500

@deals_bp.route('/<int:deal_id>', methods=['GET'])
def get_deal(deal_id):
    """Get specific deal by ID"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()

        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404

        return jsonify({
            'success': True,
            'deal': deal.to_dict()
        })

    except Exception as e:
        logging.error(f"Error fetching deal {deal_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching deal: {str(e)}'}), 500

@deals_bp.route('/', methods=['POST'])
def create_deal():
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

@deals_bp.route('/<int:deal_id>', methods=['PUT'])
def update_deal(deal_id):
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

@deals_bp.route('/<int:deal_id>', methods=['DELETE'])
def delete_deal(deal_id):
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

@deals_bp.route('/stats', methods=['GET'])
def get_deals_stats():
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

@deals_bp.route('/symbols', methods=['GET'])
def get_deal_symbols():
    """Get unique symbols from user deals"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get unique symbols
        symbols = db.session.query(UserDeal.symbol).filter_by(user_id=user_id).distinct().all()
        symbol_list = [symbol[0] for symbol in symbols]

        return jsonify({
            'success': True,
            'symbols': sorted(symbol_list)
        })

    except Exception as e:
        logging.error(f"Error fetching symbols: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching symbols: {str(e)}'}), 500