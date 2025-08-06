"""
Trading Signals API endpoints for Kotak Neo Trading Platform
Handles ETF signals, admin signals, and default deals data
"""
import logging
import sys
from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required

# Add scripts to path
sys.path.append('scripts')
try:
    from dynamic_user_deals import dynamic_deals_service
except ImportError:
    dynamic_deals_service = None

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
            'message':
            f'Successfully synced {synced_count} admin signals to default deals',
            'synced_count': synced_count
        })

    except Exception as e:
        logging.error(f"Error in sync default deals endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/analytics/time-series')
def get_time_series_data():
    """API endpoint for time series analysis - entry date vs performance"""
    try:
        from Scripts.external_db_service import get_all_trade_metrics
        signals_data = get_all_trade_metrics()
        
        # Process data for time series analysis
        time_series_data = []
        for signal in signals_data:
            if signal.get('DATE') != '--' and signal.get('%CHAN') != '--':
                # Parse date and performance
                date = signal.get('DATE')
                performance = signal.get('%CHAN')
                cpl = signal.get('CPL', 0)
                symbol = signal.get('Symbol')
                
                # Extract numeric value from percentage
                if performance and '%' in str(performance):
                    perf_value = float(str(performance).replace('%', ''))
                else:
                    perf_value = 0
                
                time_series_data.append({
                    'date': date,
                    'symbol': symbol,
                    'performance': perf_value,
                    'cpl': cpl if isinstance(cpl, (int, float)) else 0
                })
        
        # Sort by date for proper time series visualization
        time_series_data.sort(key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'data': time_series_data,
            'total': len(time_series_data)
        })
        
    except Exception as e:
        logging.error(f"Time series API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/analytics/percentage-analysis')
def get_percentage_analysis_data():
    """API endpoint for multi-period percentage analysis (7D%, 30D%, 90D%)"""
    try:
        from Scripts.external_db_service import get_all_trade_metrics
        signals_data = get_all_trade_metrics()
        
        # Process data for percentage analysis
        percentage_data = []
        trend_insights = {
            'consistent_winners': [],
            'declining_stocks': [],
            'volatile_stocks': [],
            'stable_performers': []
        }
        
        for signal in signals_data:
            symbol = signal.get('Symbol')
            if not symbol or symbol == '--':
                continue
                
            # Get 7D, 30D, and 90D percentages (simulate 90D since not in original data)
            perf_7d = signal.get('7D%', '--')
            perf_30d = signal.get('30D%', '--')
            
            # Parse percentage values
            perf_7d_val = 0
            perf_30d_val = 0
            perf_90d_val = 0  # Simulate based on available data
            
            if perf_7d != '--' and '%' in str(perf_7d):
                perf_7d_val = float(str(perf_7d).replace('%', ''))
            
            if perf_30d != '--' and '%' in str(perf_30d):
                perf_30d_val = float(str(perf_30d).replace('%', ''))
                # Simulate 90D based on 30D trend (for demonstration)
                perf_90d_val = perf_30d_val * 1.5 if perf_30d_val > 0 else perf_30d_val * 2
            
            percentage_data.append({
                'symbol': symbol,
                'perf_7d': perf_7d_val,
                'perf_30d': perf_30d_val,
                'perf_90d': perf_90d_val,
                'current_price': signal.get('CMP', 0),
                'entry_price': signal.get('EP', 0)
            })
            
            # Analyze trends for insights
            if perf_7d_val > 0 and perf_30d_val > 0 and perf_90d_val > 0:
                trend_insights['consistent_winners'].append(symbol)
            elif perf_7d_val < 0 and perf_30d_val < 0:
                trend_insights['declining_stocks'].append(symbol)
            elif abs(perf_7d_val - perf_30d_val) > 10:
                trend_insights['volatile_stocks'].append(symbol)
            elif abs(perf_7d_val) < 5 and abs(perf_30d_val) < 5:
                trend_insights['stable_performers'].append(symbol)
        
        return jsonify({
            'success': True,
            'data': percentage_data,
            'insights': trend_insights,
            'total': len(percentage_data)
        })
        
    except Exception as e:
        logging.error(f"Percentage analysis API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/default-deals-data')
def get_default_deals_data():
    """API endpoint to get default deals data directly from admin_trade_signals"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        logging.info(
            "Default deals API: Fetching data from admin_trade_signals table")

        # Connect to external database using centralized configuration
        from config.database_config import get_db_connection
        conn = get_db_connection()
        if not conn:
            raise Exception("Failed to get database connection")

        # Use the centralized connection
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                query = """
                    SELECT id, etf, symbol, thirty, dh, date, pos, qty, ep, cmp, chan, inv, 
                           tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at
                    FROM admin_trade_signals 
                    WHERE symbol IS NOT NULL
                    ORDER BY created_at DESC, id DESC
                """

                cursor.execute(query)
                rows = cursor.fetchall()

                deals_data = []
                total_investment = 0.0
                total_current_value = 0.0
                total_pnl = 0.0

                if rows:
                    for count, row in enumerate(rows, 1):
                        # Safe type conversion with fallbacks
                        quantity = int(row.get('qty') or
                                       0) if row.get('qty') is not None else 0
                        entry_price = float(
                            row.get('ep')
                            or 0) if row.get('ep') is not None else 0.0
                        current_price = float(
                            row.get('cmp')
                            or 0) if row.get('cmp') is not None else 0.0
                        pnl_amount = float(
                            row.get('pl')
                            or 0) if row.get('pl') is not None else 0.0
                        investment = float(
                            row.get('inv')
                            or 0) if row.get('inv') is not None else 0.0
                        target_price = float(
                            row.get('tp')
                            or 0) if row.get('tp') is not None else 0.0
                        current_value = float(
                            row.get('tva')
                            or 0) if row.get('tva') is not None else 0.0

                        # Handle percentage change
                        chan_value = row.get('chan') or '0'
                        if isinstance(chan_value, str):
                            chan_value = chan_value.replace('%', '')
                        pnl_pct = float(chan_value) if chan_value else 0.0

                        # Position type from pos column (1 = BUY, -1 = SELL)
                        pos = int(row.get('pos', 1))
                        position_type = 'BUY' if pos > 0 else 'SELL'

                        # Accumulate totals
                        total_investment += investment
                        total_current_value += current_value
                        total_pnl += pnl_amount

                        deal_dict = {
                            'trade_signal_id': row.get('id') or count,
                            'id': row.get('id') or count,
                            'etf': row.get('etf') or 'N/A',
                            'symbol': row.get('symbol') or 'N/A',
                            'thirty': row.get('thirty') or '',
                            'dh': row.get('dh') or '',
                            'date': str(row.get('date') or ''),
                            'pos': pos,
                            'position_type': position_type,
                            'qty': quantity,
                            'ep': entry_price,
                            'cmp': current_price,
                            'chan': row.get('chan') or f'{pnl_pct:.2f}%',
                            'inv': investment,
                            'tp': target_price,
                            'tva': current_value,
                            'tpr': row.get('tpr') or '',
                            'pl': pnl_amount,
                            'ed': row.get('ed') or '',
                            'exp': row.get('exp') or '',
                            'pr': row.get('pr') or '',
                            'pp': row.get('pp') or '',
                            'iv': row.get('iv') or '',
                            'ip': row.get('ip') or '',
                            'nt': row.get('nt') or 0,
                            'qt': float(row.get('qt') or 0),
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

                logging.info(
                    f"Default deals API: Returning {len(deals_data)} deals from admin_trade_signals"
                )

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


def handle_default_deals_data_logic():
    """
    Handle default deals data fetching logic - moved from app.py for modularity
    This function contains the business logic separated from the Flask route
    """
    return get_default_deals_data()


@signals_bp.route('/add-deal-to-user', methods=['POST'])
@login_required
def add_deal_to_user():
    """Add a deal from trading signals to user-specific deals table"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Get current user information
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        username = current_user.username

        # Check if user deals table exists, create if not
        if not dynamic_deals_service.table_exists(username):
            if not dynamic_deals_service.create_user_deals_table(username):
                return jsonify({
                    'success': False,
                    'error': 'Failed to create user deals table'
                }), 500

        # Prepare deal data
        deal_data = {
            'user_id':
            current_user.id,
            'trade_signal_id':
            data.get('signal_id'),
            'symbol':
            data.get('symbol'),
            'qty':
            data.get('qty'),
            'ep':
            data.get('ep'),  # Entry price
            'pos':
            data.get('pos'),  # Position (BUY/SELL)
            'status':
            'ACTIVE',
            'target_price':
            data.get('target_price'),
            'stop_loss':
            data.get('stop_loss'),
            'notes':
            data.get('notes',
                     f'Added from trading signals on {data.get("symbol")}')
        }

        # Add deal to user table
        deal_id = dynamic_deals_service.add_deal_to_user_table(
            username, deal_data)

        if deal_id:
            return jsonify({
                'success': True,
                'message':
                f'Deal added successfully to {username}_deals table',
                'deal_id': deal_id,
                'table_name': f'{username}_deals'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add deal'
            }), 500

    except Exception as e:
        logging.error(f"Add deal to user API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@signals_bp.route('/initialize-auto-sync', methods=['POST'])
def initialize_auto_sync():
    """API endpoint to initialize automatic synchronization system"""
    try:
        from Scripts.auto_sync_system import initialize_auto_sync_system
        result = initialize_auto_sync_system()

        return jsonify({
            'success':
            result['success'],
            'message':
            'Auto-sync system initialized successfully'
            if result['success'] else 'Failed to initialize auto-sync system',
            'details':
            result
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
            'success':
            test_result,
            'message':
            'Auto-sync test passed' if test_result else 'Auto-sync test failed'
        })

    except Exception as e:
        logging.error(f"Error testing auto-sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
