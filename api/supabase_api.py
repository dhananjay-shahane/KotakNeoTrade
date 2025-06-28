
from flask import Blueprint, request, jsonify, session
import logging
from Scripts.supabase_client import supabase_client
from datetime import datetime

supabase_bp = Blueprint('supabase_api', __name__)

@supabase_bp.route('/supabase/status')
def supabase_status():
    """Check Supabase connection status"""
    try:
        is_connected = supabase_client.is_connected()
        return jsonify({
            'success': True,
            'connected': is_connected,
            'message': 'Supabase is connected' if is_connected else 'Supabase not configured'
        })
    except Exception as e:
        logging.error(f"Error checking Supabase status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/supabase/sync-users')
def sync_users():
    """Sync users between local database and Supabase"""
    try:
        if not supabase_client.is_connected():
            return jsonify({'success': False, 'error': 'Supabase not connected'}), 400
        
        # Get users from Supabase
        supabase_users = supabase_client.get_users()
        
        # Get local users
        from Scripts.models import User
        local_users = User.query.all()
        
        sync_stats = {
            'supabase_users': len(supabase_users),
            'local_users': len(local_users),
            'synced': 0,
            'errors': 0
        }
        
        # Sync local users to Supabase
        for user in local_users:
            try:
                user_data = {
                    'ucc': user.ucc,
                    'mobile_number': user.mobile_number,
                    'greeting_name': user.greeting_name,
                    'user_id': user.user_id,
                    'client_code': user.client_code,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Check if user exists in Supabase
                existing = next((u for u in supabase_users if u.get('ucc') == user.ucc), None)
                
                if existing:
                    # Update existing user
                    supabase_client.update_user(existing['id'], user_data)
                else:
                    # Create new user
                    supabase_client.create_user(user_data)
                
                sync_stats['synced'] += 1
                
            except Exception as e:
                logging.error(f"Error syncing user {user.ucc}: {e}")
                sync_stats['errors'] += 1
        
        return jsonify({
            'success': True,
            'message': 'User sync completed',
            'stats': sync_stats
        })
        
    except Exception as e:
        logging.error(f"Error syncing users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/supabase/sync-signals')
def sync_signals():
    """Sync ETF signals between local database and Supabase"""
    try:
        if not supabase_client.is_connected():
            return jsonify({'success': False, 'error': 'Supabase not connected'}), 400
        
        # Get signals from Supabase
        supabase_signals = supabase_client.get_etf_signals(limit=100)
        
        # Get local signals
        from Scripts.models_etf import AdminTradeSignal
        local_signals = AdminTradeSignal.query.limit(100).all()
        
        sync_stats = {
            'supabase_signals': len(supabase_signals),
            'local_signals': len(local_signals),
            'synced': 0,
            'errors': 0
        }
        
        # Sync local signals to Supabase
        for signal in local_signals:
            try:
                signal_data = {
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'entry_price': float(signal.entry_price),
                    'current_price': float(signal.current_price) if signal.current_price else None,
                    'target_price': float(signal.target_price) if signal.target_price else None,
                    'stop_loss': float(signal.stop_loss) if signal.stop_loss else None,
                    'quantity': signal.quantity,
                    'status': signal.status,
                    'priority': signal.priority,
                    'signal_description': signal.signal_description,
                    'created_at': signal.created_at.isoformat() if signal.created_at else None,
                    'updated_at': datetime.utcnow().isoformat(),
                    'expires_at': signal.expires_at.isoformat() if signal.expires_at else None
                }
                
                # Create signal in Supabase
                supabase_client.create_etf_signal(signal_data)
                sync_stats['synced'] += 1
                
            except Exception as e:
                logging.error(f"Error syncing signal {signal.id}: {e}")
                sync_stats['errors'] += 1
        
        return jsonify({
            'success': True,
            'message': 'Signals sync completed',
            'stats': sync_stats
        })
        
    except Exception as e:
        logging.error(f"Error syncing signals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/supabase/sync-quotes')
def sync_quotes():
    """Sync real-time quotes to Supabase"""
    try:
        if not supabase_client.is_connected():
            return jsonify({'success': False, 'error': 'Supabase not connected'}), 400
        
        # Get local quotes
        from Scripts.models_etf import RealtimeQuote
        local_quotes = RealtimeQuote.query.limit(50).all()
        
        quotes_data = []
        for quote in local_quotes:
            quote_data = {
                'symbol': quote.symbol,
                'current_price': float(quote.current_price),
                'volume': int(quote.volume) if quote.volume else 0,
                'change_percent': float(quote.change_percent) if quote.change_percent else 0,
                'timestamp': quote.timestamp.isoformat() if quote.timestamp else datetime.utcnow().isoformat()
            }
            quotes_data.append(quote_data)
        
        # Bulk insert to Supabase
        success = supabase_client.bulk_insert_quotes(quotes_data)
        
        return jsonify({
            'success': success,
            'message': f'Synced {len(quotes_data)} quotes to Supabase' if success else 'Failed to sync quotes',
            'quotes_synced': len(quotes_data) if success else 0
        })
        
    except Exception as e:
        logging.error(f"Error syncing quotes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/supabase/create-signal', methods=['POST'])
def create_signal():
    """Create new ETF signal in Supabase"""
    try:
        if not supabase_client.is_connected():
            return jsonify({'success': False, 'error': 'Supabase not connected'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['symbol', 'signal_type', 'entry_price', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Add metadata
        signal_data = {
            **data,
            'created_at': datetime.utcnow().isoformat(),
            'status': data.get('status', 'ACTIVE'),
            'priority': data.get('priority', 'MEDIUM')
        }
        
        # Create in Supabase
        result = supabase_client.create_etf_signal(signal_data)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Signal created successfully',
                'signal': result
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create signal'}), 500
        
    except Exception as e:
        logging.error(f"Error creating signal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@supabase_bp.route('/supabase/realtime-test')
def realtime_test():
    """Test real-time subscription functionality"""
    try:
        if not supabase_client.is_connected():
            return jsonify({'success': False, 'error': 'Supabase not connected'}), 400
        
        def signal_callback(payload):
            logging.info(f"Real-time signal update: {payload}")
        
        def quote_callback(payload):
            logging.info(f"Real-time quote update: {payload}")
        
        # Subscribe to real-time updates
        signal_subscription = supabase_client.subscribe_to_signals(signal_callback)
        quote_subscription = supabase_client.subscribe_to_quotes(quote_callback)
        
        return jsonify({
            'success': True,
            'message': 'Real-time subscriptions activated',
            'signal_subscription': signal_subscription is not None,
            'quote_subscription': quote_subscription is not None
        })
        
    except Exception as e:
        logging.error(f"Error testing real-time: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
