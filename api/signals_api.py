"""
Trading Signals API endpoints for Kotak Neo Trading Platform
Handles ETF signals, admin signals, and default deals data
"""
import logging
from flask import Blueprint, jsonify, request

# Create blueprint for signals API
signals_bp = Blueprint('signals_api', __name__, url_prefix='/api')


@signals_bp.route('/etf-signals-data')
def get_etf_signals_data():
    """API endpoint to get ETF signals data from external admin_trade_signals table"""
    try:
        from Scripts.external_db_service import get_etf_signals_data_json
        return jsonify(get_etf_signals_data_json())
    except Exception as e:
        logging.error(f"ETF signals API error: {e}")
        return jsonify({'error': str(e)}), 500


@signals_bp.route('/basic-trade-signals-data')
def get_basic_trade_signals_data():
    """API endpoint to get basic trade signals data from external admin_trade_signals table"""
    try:
        from Scripts.external_db_service import get_basic_trade_signals_data_json
        return jsonify(get_basic_trade_signals_data_json())
    except Exception as e:
        logging.error(f"Basic trade signals API error: {e}")
        return jsonify({'error': str(e)}), 500


@signals_bp.route('/sync-default-deals', methods=['POST'])
def sync_default_deals():
    """API endpoint to sync all admin_trade_signals to default_deals table"""
    try:
        from Scripts.default_deals_sync import sync_admin_signals_to_default_deals
        synced_count = sync_admin_signals_to_default_deals()

        return jsonify({
            'success': True,
            'message': f'Successfully synced {synced_count} admin signals to default deals',
            'synced_count': synced_count
        })

    except Exception as e:
        logging.error(f"Error in sync default deals endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/default-deals-data')
def get_default_deals_data():
    """API endpoint to get default deals data directly from admin_trade_signals"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        logging.info("Default deals API: Fetching data from admin_trade_signals table")

        # Connect to external database using the same connection as ETF signals
        connection_string = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"

        # Connect to external database
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                query = """
                    SELECT id, etf, symbol, thirty, dh, date, pos, qty, ep, cmp, chan, inv, 
                           tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at
                    FROM admin_trade_signals 
                    WHERE symbol IS NOT NULL
                    ORDER BY created_at DESC, id DESC
                """

                cursor.execute(query)
                signals = cursor.fetchall()

                # Format signals as default deals data for frontend
                deals_data = []
                total_investment = 0
                total_current_value = 0
                total_pnl = 0

                for row in signals:
                    # Calculate values with proper null handling
                    entry_price = float(row.get('ep') or 0) if row.get('ep') is not None else 0.0
                    current_price = float(row.get('cmp') or 0) if row.get('cmp') is not None else 0.0
                    quantity = int(row.get('qty') or 0) if row.get('qty') is not None else 0
                    investment = float(row.get('inv') or 0) if row.get('inv') is not None else 0.0
                    pnl_amount = float(row.get('pl') or 0) if row.get('pl') is not None else 0.0
                    target_price = float(row.get('tp') or 0) if row.get('tp') is not None else 0.0

                    # Calculate derived values
                    current_value = current_price * quantity if current_price > 0 and quantity > 0 else 0.0
                    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 and current_price > 0 else 0.0

                    # Update totals
                    total_investment += investment
                    total_current_value += current_value
                    total_pnl += pnl_amount

                    # Create deal dictionary with all columns preserved
                    deal_dict = {
                        # Original CSV columns preserved
                        'id': row.get('id'),
                        'etf': row.get('etf') or '',
                        'symbol': row.get('symbol') or '',
                        'thirty': row.get('thirty') or '',
                        'dh': row.get('dh') or '',
                        'date': str(row.get('date') or ''),
                        'pos': row.get('pos') or '',
                        'qty': quantity,
                        'ep': entry_price,
                        'cmp': current_price,
                        'chan': row.get('chan') or '',
                        'inv': investment,
                        'tp': target_price,
                        'tva': row.get('tva') or '',
                        'tpr': row.get('tpr') or '',
                        'pl': pnl_amount,
                        'ed': row.get('ed') or '',
                        'exp': row.get('exp') or '',
                        'pr': row.get('pr') or '',
                        'pp': row.get('pp') or '',
                        'iv': row.get('iv') or '',
                        'ip': row.get('ip') or '',
                        'nt': row.get('nt') or '',
                        'qt': row.get('qt') or '',
                        'seven': row.get('seven') or '',
                        'ch': row.get('ch') or '',
                        'created_at': str(row.get('created_at') or ''),
                        # Standard fields for compatibility
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'quantity': quantity,
                        'investment_amount': investment,
                        'target_price': target_price,
                        'total_value': current_value,
                        'pnl': pnl_amount,
                        'price_change_percent': pnl_pct,
                        'entry_date': str(row.get('date') or ''),
                        'admin_signal_id': row.get('id'),
                        'status': 'ACTIVE'
                    }
                    deals_data.append(deal_dict)

        logging.info(f"Default deals API: Returning {len(deals_data)} deals from admin_trade_signals")

        return jsonify({
            'success': True,
            'data': deals_data,
            'total_count': len(deals_data),
            'portfolio': {
                'total_investment': total_investment,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'total_positions': len(deals_data)
            }
        })

    except Exception as e:
        logging.error(f"Error fetching default deals data: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'data': []}), 500


@signals_bp.route('/initialize-auto-sync', methods=['POST'])
def initialize_auto_sync():
    """API endpoint to initialize automatic synchronization system"""
    try:
        from Scripts.auto_sync_system import initialize_auto_sync_system
        result = initialize_auto_sync_system()

        return jsonify({
            'success': result['success'],
            'message': 'Auto-sync system initialized successfully' if result['success'] else 'Failed to initialize auto-sync system',
            'details': result
        })

    except Exception as e:
        logging.error(f"Error initializing auto-sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/test-auto-sync', methods=['POST'])
def test_auto_sync():
    """API endpoint to test automatic synchronization"""
    try:
        from Scripts.auto_sync_system import test_auto_sync
        test_result = test_auto_sync()

        return jsonify({
            'success': test_result,
            'message': 'Auto-sync test passed' if test_result else 'Auto-sync test failed'
        })

    except Exception as e:
        logging.error(f"Error testing auto-sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500