"""
Deals API - Clean version without PostgreSQL dependencies
Handles all deals-related operations with simple local JSON storage
"""
import logging
from flask import Blueprint, request, jsonify, session
import json
import os
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

deals_api = Blueprint('deals_api', __name__, url_prefix='/api')

@deals_api.route('/test-deals', methods=['GET'])
def test_deals():
    """Test endpoint to verify blueprint registration"""
    return jsonify({
        'message': 'Deals API blueprint is working',
        'success': True
    })

def get_user_deals_from_local():
    """
    Get user deals from local JSON file storage
    Returns all authentic deals with proper structure for calculations
    """
    try:
        deals_file = 'user_deals.json'
        
        if not os.path.exists(deals_file):
            logger.info("No deals file found, returning empty list")
            return []

        with open(deals_file, 'r') as f:
            all_deals = json.load(f)

        # Filter and return active deals
        deals = []
        for deal in all_deals:
            if deal.get('status') == 'ACTIVE':
                # Ensure numeric fields are properly formatted
                deal['entry_price'] = float(deal.get('entry_price', 0))
                deal['current_price'] = float(deal.get('current_price', 0))
                deal['invested_amount'] = float(deal.get('invested_amount', 0))
                deal['current_value'] = float(deal.get('current_value', 0))
                deal['pnl_amount'] = float(deal.get('pnl_amount', 0))
                deal['pnl_percent'] = float(deal.get('pnl_percent', 0))
                deals.append(deal)
        
        logger.info(f"✓ Fetched {len(deals)} user deals from local storage")
        return deals

    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        return []

@deals_api.route('/user-deals-data')
def get_user_deals_data():
    """API endpoint to get user deals data from local storage"""
    try:
        deals = get_user_deals_from_local()
        
        # Calculate summary
        total_invested = sum(deal.get('invested_amount', 0) for deal in deals)
        total_current = sum(deal.get('current_value', 0) for deal in deals)
        total_pnl = total_current - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            'success': True,
            'deals': deals,
            'summary': {
                'total_deals': len(deals),
                'total_invested': total_invested,
                'total_current_value': total_current,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent
            }
        })
        
    except Exception as e:
        logger.error(f"Error in user deals API: {e}")
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

@deals_api.route('/deals/create-from-signal', methods=['POST'])
def create_deal_from_signal():
    """Create a new deal from trading signal using local JSON storage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Extract signal data
        signal_data = data.get('signal_data', {})
        
        # Helper functions for safe conversion
        def safe_float(value, default=0.0):
            if value is None or value == '' or value == '--':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=1):
            if value is None or value == '':
                return default
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default

        # Get required fields with safe conversion
        symbol = signal_data.get('symbol') or signal_data.get('etf', '')
        if not symbol or symbol == 'UNKNOWN':
            return jsonify({
                'success': False,
                'error': 'Missing or invalid symbol'
            }), 400

        qty = safe_int(signal_data.get('qty'), 1)
        ep = safe_float(signal_data.get('ep'), 0.0)
        cmp = signal_data.get('cmp')
        
        # Handle CMP - if it's "--" or invalid, use entry price
        if cmp == "--" or cmp is None or cmp == '':
            cmp = ep
        else:
            cmp = safe_float(cmp, ep)
        
        pos = safe_int(signal_data.get('pos'), 1)
        
        # Set user_id - handle both string and integer user_ids safely
        session_user_id = session.get('user_id', 1)
        
        # Convert user_id to integer safely, fallback to 1 if invalid
        try:
            if isinstance(session_user_id, str):
                if session_user_id.isdigit():
                    user_id = int(session_user_id)
                else:
                    logger.info(f"Non-numeric user_id in session: {session_user_id}, using default user_id = 1")
                    user_id = 1
            elif isinstance(session_user_id, int):
                user_id = session_user_id
            else:
                user_id = 1
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id in session: {session_user_id}, using default user_id = 1")
            user_id = 1

        # Validate required data
        if ep <= 0 or qty <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid price or quantity data'
            }), 400

        if not symbol or len(symbol.strip()) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid symbol'
            }), 400

        if user_id <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid user ID'
            }), 400

        # Calculate target price safely
        tp = safe_float(signal_data.get('tp'), ep * 1.05)
        if tp <= 0:
            tp = ep * 1.05

        # Calculate values
        invested_amount = ep * qty
        current_value = cmp * qty
        pnl_amount = current_value - invested_amount
        pnl_percent = (pnl_amount / invested_amount * 100) if invested_amount > 0 else 0

        # Use local JSON file storage
        deals_file = 'user_deals.json'
        
        # Ensure user_id is positive
        if not user_id or user_id <= 0:
            user_id = 1

        # Load existing deals or create new file
        if os.path.exists(deals_file):
            with open(deals_file, 'r') as f:
                all_deals = json.load(f)
        else:
            all_deals = []

        # Create new deal record
        deal_id = len(all_deals) + 1
        new_deal = {
            'id': deal_id,
            'user_id': user_id,
            'symbol': symbol.upper(),
            'trading_symbol': symbol.upper(),
            'entry_date': datetime.now().strftime('%Y-%m-%d'),
            'position_type': 'LONG' if pos == 1 else 'SHORT',
            'quantity': qty,
            'entry_price': float(ep),
            'current_price': float(cmp),
            'target_price': float(tp),
            'stop_loss': float(ep * 0.95),  # Default 5% stop loss
            'invested_amount': float(invested_amount),
            'current_value': float(current_value),
            'pnl_amount': float(pnl_amount),
            'pnl_percent': float(pnl_percent),
            'status': 'ACTIVE',
            'deal_type': 'SIGNAL',
            'notes': f'Added from ETF signal - {symbol}',
            'tags': 'ETF,SIGNAL',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        all_deals.append(new_deal)

        # Save to JSON file
        with open(deals_file, 'w') as f:
            json.dump(all_deals, f, indent=2)

        logger.info(f"✓ Created deal from signal: {symbol} - Deal ID: {deal_id} for user: {user_id}")

        return jsonify({
            'success': True,
            'message': f'Deal created successfully for {symbol}',
            'deal_id': deal_id,
            'symbol': symbol,
            'entry_price': ep,
            'quantity': qty,
            'invested_amount': invested_amount
        })

    except Exception as db_error:
        logger.error(f"Database error creating deal: {db_error}")
        logger.error(f"Signal data was: {signal_data}")
        logger.error(f"Processed values were: user_id={user_id}, symbol={symbol}, qty={qty}, ep={ep}, cmp={cmp}")
        return jsonify({
            'success': False,
            'error': f'Failed to create deal: {str(db_error)}'
        }), 500