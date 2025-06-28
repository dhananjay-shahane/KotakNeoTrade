"""Fix calculate_pnl method calls in deals API and handle potential calculation errors."""
from flask import Blueprint, request, jsonify, session
from Scripts.models import db, User
from Scripts.models_etf import AdminTradeSignal, UserDeal, UserNotification
import json
from datetime import datetime
import logging
from functools import wraps

deals_bp = Blueprint('deals', __name__, url_prefix='/api/deals')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'ucc' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

@deals_bp.route('/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a new deal from ETF signal data"""
    try:
        # Check if user is logged in - try multiple session keys or use default user
        user_id = session.get('user_id') or session.get('db_user_id') or session.get('ucc')
        if not user_id:
            # For testing, use default user ID 1 if no session
            user_id = 1
            logging.info("Using default user ID 1 for deal creation")

        # If ucc is used, try to find or create user record
        if user_id == session.get('ucc'):
            from Scripts.models import User
            user = User.query.filter_by(ucc=user_id).first()
            if user:
                user_id = user.id
            else:
                # Create user record if doesn't exist
                user = User(
                    ucc=user_id,
                    mobile_number=session.get('mobile_number', ''),
                    greeting_name=session.get('greeting_name', user_id),
                    user_id=user_id,
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                user_id = user.id
        data = request.get_json()

        # Extract complete signal data
        signal_data = data.get('signal_data', {})

        # Helper function to safely convert values
        def safe_float(value, default=0.0):
            try:
                if value is None or value == '':
                    return default
                # Handle percentage strings like '-1.91%'
                if isinstance(value, str) and '%' in value:
                    return float(value.replace('%', ''))
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                if value is None or value == '':
                    return default
                return int(float(value))  # Convert to float first to handle decimal strings
            except (ValueError, TypeError):
                return default

        # Extract all signal fields exactly as they appear
        trade_signal_id = str(signal_data.get('trade_signal_id', ''))
        etf_symbol = signal_data.get('etf') or signal_data.get('symbol', 'UNKNOWN')
        symbol = signal_data.get('symbol') or signal_data.get('etf', 'UNKNOWN')
        pos = safe_int(signal_data.get('pos', 1))
        qty = safe_int(signal_data.get('qty', 1))
        ep = safe_float(signal_data.get('ep', 0))
        cmp = safe_float(signal_data.get('cmp', 0)) or ep
        tp = safe_float(signal_data.get('tp', 0)) if signal_data.get('tp') else None
        inv = safe_float(signal_data.get('inv', 0)) or (ep * qty)
        pl = safe_float(signal_data.get('pl', 0))
        
        # Create new deal with complete ETF signal data
        deal = UserDeal(
            user_id=user_id,
            # ETF Signal specific fields
            trade_signal_id=trade_signal_id,
            etf_symbol=etf_symbol.upper(),
            symbol=symbol.upper(),
            trading_symbol=symbol.upper(),
            exchange='NSE',
            pos=pos,
            qty=qty,
            ep=ep,
            cmp=cmp,
            tp=tp,
            inv=inv,
            pl=pl,
            chan_percent=str(signal_data.get('change_pct', signal_data.get('chan', ''))),
            thirty=str(signal_data.get('thirty', '')),
            dh=int(signal_data.get('dh', 0)),
            signal_date=str(signal_data.get('date', '')),
            ed=str(signal_data.get('ed', '')),
            exp=str(signal_data.get('exp', '')),
            pr=str(signal_data.get('pr', '')),
            pp=str(signal_data.get('pp', '')),
            iv=str(signal_data.get('iv', '')),
            ip=str(signal_data.get('ip', '')),
            nt=str(signal_data.get('nt', 'Added from ETF signals')),
            qt=str(signal_data.get('qt', '')),
            seven=str(signal_data.get('seven', '')),
            ch=str(signal_data.get('ch', '')),
            tva=safe_float(signal_data.get('tva', 0)) if signal_data.get('tva') else None,
            tpr=safe_float(signal_data.get('tpr', 0)) if signal_data.get('tpr') else None,
            
            # Standard deal fields for compatibility
            position_type='LONG' if pos == 1 else 'SHORT',
            quantity=qty,
            entry_price=ep,
            current_price=cmp,
            target_price=tp,
            stop_loss=ep * 0.95,  # Default 5% stop loss
            invested_amount=inv,
            notes=f'Added from ETF signals - {signal_data.get("nt", "")}',
            tags='ETF_SIGNAL',
            deal_type='SIGNAL'
        )

        # Set current price to entry price initially
        deal.current_price = ep

        # Calculate initial P&L
        try:
            deal.calculate_pnl()
        except Exception as calc_error:
            logging.warning(f"Could not calculate P&L for new deal: {calc_error}")
            deal.pnl_amount = 0.0
            deal.pnl_percent = 0.0

        db.session.add(deal)
        db.session.commit()

        logging.info(f"Deal created from signal for user {user_id}: {deal.symbol} {deal.position_type}")

        return jsonify({
            'success': True,
            'message': 'Deal created successfully from signal',
            'deal_id': deal.id,
            'deal': deal.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating deal from signal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating deal: {str(e)}'}), 500

@deals_bp.route('/create', methods=['POST'])
def create_deal():
    """Create a new deal from a trade signal"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        user_id = session['user_id']
        data = request.get_json()

        # Validate required fields
        required_fields = ['symbol', 'position_type', 'quantity', 'entry_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Calculate invested amount
        quantity = int(data['quantity'])
        entry_price = float(data['entry_price'])
        invested_amount = quantity * entry_price

        # Create new deal
        deal = UserDeal(
            user_id=user_id,
            signal_id=data.get('signal_id'),
            symbol=data['symbol'].upper(),
            trading_symbol=data.get('trading_symbol', data['symbol'].upper()),
            exchange=data.get('exchange', 'NSE'),
            position_type=data['position_type'].upper(),
            quantity=quantity,
            entry_price=entry_price,
            current_price=float(data.get('current_price', entry_price)),
            target_price=float(data['target_price']) if data.get('target_price') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            invested_amount=invested_amount,
            notes=data.get('notes', ''),
            tags=data.get('tags', ''),
            deal_type='SIGNAL' if data.get('signal_id') else 'MANUAL'
        )

        # Set current price to entry price initially
        deal.current_price = entry_price

        # Calculate initial P&L
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
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating deal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating deal: {str(e)}'}), 500
@deals_bp.route('/user', methods=['GET'])
def get_user_deals():
    """Get deals for the current user from external database only"""
    try:
        # Check session for user authentication
        user_ucc = session.get('ucc')
        user_id = session.get('user_id') or session.get('db_user_id')

        if not user_ucc and not user_id:
            logging.warning("No authenticated user found in session")
            return jsonify({
                'success': True,
                'deals': [],
                'total_deals': 0,
                'message': 'No authenticated user found'
            })

        deals_data = []

        # Get deals from database only - no CSV fallback
        try:
            from Scripts.models import User
            from Scripts.models_etf import UserDeal

            current_user = None

            # Try to find user by UCC first, then by user_id
            if user_ucc:
                current_user = User.query.filter_by(ucc=user_ucc).first()
                logging.info(f"Looking for user with UCC: {user_ucc}")

            if not current_user and user_id:
                current_user = User.query.get(user_id)
                logging.info(f"Looking for user with ID: {user_id}")

            if current_user:
                logging.info(f"Found user: {current_user.id} with UCC: {current_user.ucc}")
                db_deals = UserDeal.query.filter_by(user_id=current_user.id).order_by(UserDeal.created_at.desc()).all()

                # Convert database deals to response format
                for deal in db_deals:
                    try:
                        deal_dict = deal.to_dict()
                        deals_data.append(deal_dict)
                    except Exception as deal_error:
                        logging.error(f"Error converting deal {deal.id} to dict: {deal_error}")
                        continue

                logging.info(f"Found {len(db_deals)} deals in database for user {current_user.ucc}")
            else:
                logging.warning(f"No user found for UCC: {user_ucc} or ID: {user_id}")
                # Check if there are any users in the database
                total_users = User.query.count()
                total_deals = UserDeal.query.count()
                logging.info(f"Total users in database: {total_users}, Total deals: {total_deals}")

                # If no user found but we have session data, create a default user
                if user_ucc:
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
                        current_user = new_user
                        logging.info(f"Created new user with UCC: {user_ucc}")
                    except Exception as create_error:
                        logging.error(f"Error creating new user: {create_error}")
                        db.session.rollback()

        except Exception as db_error:
            logging.error(f"Database error fetching deals: {db_error}")

        except Exception as db_error:
            logging.error(f"Database error fetching deals: {db_error}")
            return jsonify({
                'success': False, 
                'message': f'Database error: {str(db_error)}',
                'deals': []
            }), 500

        # Log the results
        logging.info(f"Returning {len(deals_data)} deals from database for user {user_ucc or user_id}")

        return jsonify({
            'success': True,
            'deals': deals_data,
            'total_deals': len(deals_data),
            'user_ucc': user_ucc or 'Unknown',
            'data_sources': ['Database'] if deals_data else ['None']
        })

    except Exception as e:
        logging.error(f"Error fetching user deals: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error fetching deals: {str(e)}',
            'deals': []
        }), 500

@deals_bp.route('/<int:deal_id>/close', methods=['POST'])
def close_deal():
    """Close a specific deal"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        user_id = session['user_id']
        deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()

        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404

        data = request.get_json()
        exit_price = float(data.get('exit_price', deal.current_price))

        # Update deal with exit information
        deal.current_price = exit_price
        deal.status = 'CLOSED'
        deal.exit_date = datetime.utcnow()
        deal.updated_at = datetime.utcnow()

        # Calculate initial P&L
        try:
            deal.calculate_pnl()
        except Exception as calc_error:
            logging.warning(f"Could not calculate P&L for deal: {calc_error}")
            deal.pnl_amount = 0.0
            deal.pnl_percent = 0.0

        if data.get('notes'):
            deal.notes = (deal.notes or '') + f"\nClosed: {data['notes']}"

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Deal closed successfully',
            'deal': deal.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error closing deal: {str(e)}")
        return jsonify({'success': False, 'message': f'Error closing deal: {str(e)}'}), 500

@deals_bp.route('/<int:deal_id>/update', methods=['PUT'])
def update_deal():
    """Update a specific deal"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        user_id = session['user_id']
        deal = UserDeal.query.filter_by(id=deal_id, user_id=user_id).first()

        if not deal:
            return jsonify({'success': False, 'message': 'Deal not found'}), 404

        data = request.get_json()

        # Update allowed fields
        if 'target_price' in data:
            deal.target_price = float(data['target_price']) if data['target_price'] else None

        if 'stop_loss' in data:
            deal.stop_loss = float(data['stop_loss']) if data['stop_loss'] else None

        if 'notes' in data:
            deal.notes = data['notes']

        if 'tags' in data:
            deal.tags = data['tags']

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

@deals_bp.route('/stats', methods=['GET'])
def get_deals_stats():
    """Get deals statistics for current user - only real data"""
    try:
        # Check if user is logged in or use default  
        user_id = session.get('user_id') or session.get('db_user_id') or session.get('ucc')
        if not user_id:
            user_id = 1  # Default user for testing

        deals = UserDeal.query.filter_by(user_id=user_id).all()

        # Only return stats from real database deals - no sample data
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
        if stats['total_deals'] > 0:
            stats['success_rate'] = (stats['winning_deals'] / stats['total_deals']) * 100
        else:
            stats['success_rate'] = 0

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logging.error(f"Error fetching deals stats: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching stats: {str(e)}'}), 500