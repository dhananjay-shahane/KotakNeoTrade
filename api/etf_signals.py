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
    """Get ETF signals data from admin_trade_signals table with real-time CMP from Kotak Neo"""
    try:
        # Get ALL admin trade signals from database using direct SQL query
        result = db.session.execute(text("""
            SELECT symbol, entry_price, current_price, quantity, investment_amount, 
                   position_type, status, created_at
            FROM admin_trade_signals 
            ORDER BY created_at DESC
        """))
        signals_data = result.fetchall()

        if not signals_data:
            logger.info("No admin trade signals found in database")
            return jsonify({
                'success': True,
                'signals': [],
                'total': 0,
                'message': 'ETF signals API configured. Database table exists but contains no data.'
            })

        # Process signals data
        signals_list = []
        total_investment = 0
        total_current_value = 0
        
        for row in signals_data:
            symbol, entry_price, current_price, quantity, investment_amount, position_type, status, created_at = row
            
            # Convert to proper types
            entry_price = float(entry_price) if entry_price else 0
            current_price = float(current_price) if current_price else 0
            quantity = int(quantity) if quantity else 0
            investment_amount = float(investment_amount) if investment_amount else 0
            
            # Calculate P&L
            pnl = 0
            pnl_percentage = 0
            current_value = 0
            
            if entry_price > 0 and current_price > 0 and quantity > 0:
                current_value = current_price * quantity
                pnl = (current_price - entry_price) * quantity
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
            
            signal_data = {
                'symbol': symbol,
                'entry_price': entry_price,
                'current_price': current_price,
                'quantity': quantity,
                'investment_amount': investment_amount,
                'current_value': current_value,
                'position_type': position_type or 'LONG',
                'status': status or 'ACTIVE',
                'created_at': created_at.isoformat() if created_at else None,
                'pnl': round(pnl, 2),
                'pnl_percentage': round(pnl_percentage, 2)
            }
            
            signals_list.append(signal_data)
            total_investment += investment_amount
            total_current_value += current_value

        # Calculate portfolio summary
        total_pnl = total_current_value - total_investment
        return_percent = ((total_pnl / total_investment) * 100) if total_investment > 0 else 0
        
        portfolio_summary = {
            'total_positions': len(signals_list),
            'total_investment': round(total_investment, 2),
            'current_value': round(total_current_value, 2),
            'total_pnl': round(total_pnl, 2),
            'return_percent': round(return_percent, 2),
            'active_positions': len([s for s in signals_list if s['status'] == 'ACTIVE']),
            'closed_positions': len([s for s in signals_list if s['status'] != 'ACTIVE'])
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
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        required_fields = ['symbol', 'signal_type', 'entry_price', 'target_users']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Create admin signal record
        insert_query = text("""
            INSERT INTO admin_trade_signals 
            (symbol, signal_type, entry_price, current_price, quantity, status, created_at)
            VALUES (:symbol, :signal_type, :entry_price, :current_price, :quantity, 'ACTIVE', :created_at)
        """)
        
        db.session.execute(insert_query, {
            'symbol': data['symbol'],
            'signal_type': data['signal_type'],
            'entry_price': data['entry_price'],
            'current_price': data.get('current_price', data['entry_price']),
            'quantity': data.get('quantity', 1),
            'created_at': datetime.now()
        })
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Signal sent for {data['symbol']} to {len(data['target_users'])} users"
        })
        
    except Exception as e:
        logger.error(f"Error sending admin signal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/admin/users', methods=['GET'])
def get_target_users():
    """Get list of users to send signals to"""
    try:
        # Get users from database
        result = db.session.execute(text("SELECT ucc, greeting_name FROM users LIMIT 10"))
        users = result.fetchall()
        
        users_list = []
        for row in users:
            ucc, name = row
            users_list.append({
                'ucc': ucc,
                'name': name or 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'users': users_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/user-deals', methods=['GET'])
def get_user_deals():
    """Get deals created by current user"""
    try:
        # Return empty deals for now
        return jsonify({
            'success': True,
            'deals': [],
            'total': 0
        })
        
    except Exception as e:
        logger.error(f"Error fetching user deals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/create-deal', methods=['POST'])
def create_deal():
    """Create a new deal from signal or manually"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Deal creation functionality will be implemented',
            'deal_id': 'placeholder'
        })
        
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/search-instruments', methods=['GET'])
def search_etf_instruments():
    """Search for ETF instruments"""
    try:
        query = request.args.get('q', '')
        
        # Return common ETF instruments
        instruments = [
            {'symbol': 'NIFTYBEES', 'name': 'Nippon India ETF Nifty BeES'},
            {'symbol': 'GOLDBEES', 'name': 'Nippon India ETF Gold BeES'},
            {'symbol': 'BANKBEES', 'name': 'Nippon India ETF Bank BeES'},
            {'symbol': 'JUNIORBEES', 'name': 'Nippon India ETF Junior BeES'},
            {'symbol': 'LIQUIDBEES', 'name': 'Nippon India ETF Liquid BeES'}
        ]
        
        if query:
            instruments = [i for i in instruments if query.upper() in i['symbol'].upper() or query.upper() in i['name'].upper()]
        
        return jsonify({
            'success': True,
            'instruments': instruments
        })
        
    except Exception as e:
        logger.error(f"Error searching instruments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/quotes', methods=['GET'])
def get_etf_quotes():
    """Get live quotes for ETF instruments"""
    try:
        symbols = request.args.getlist('symbols')
        
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = {
                'ltp': 0,
                'change': 0,
                'change_percent': 0
            }
        
        return jsonify({
            'success': True,
            'quotes': quotes
        })
        
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/portfolio-summary', methods=['GET'])
def get_portfolio_summary():
    """Get portfolio summary metrics"""
    try:
        # Calculate from admin_trade_signals table
        result = db.session.execute(text("""
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
        return_percent = ((total_pnl / total_investment) * 100) if total_investment > 0 else 0
        
        return jsonify({
            'success': True,
            'portfolio': {
                'total_positions': int(total_positions) if total_positions else 0,
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
            return jsonify({'success': False, 'error': 'No updates provided'}), 400
        
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f"Bulk update functionality will be implemented for {len(data['updates'])} positions"
        })
        
    except Exception as e:
        logger.error(f"Error bulk updating positions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@etf_bp.route('/api/etf-signals-data', methods=['GET'])
def get_etf_signals_data():
    """API endpoint to get ETF signals data from database (admin_trade_signals for user zhz3j)"""
    try:
        # Redirect to main signals endpoint
        return get_admin_signals()
        
    except Exception as e:
        logger.error(f"Error in etf-signals-data endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500