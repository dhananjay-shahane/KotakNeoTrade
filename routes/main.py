"""Main application routes"""
from flask import Blueprint, render_template, session, flash, redirect, url_for, jsonify, request
import logging
import time
from datetime import datetime

from utils.auth import login_required, validate_current_session, is_session_expired
from Scripts.trading_functions import TradingFunctions
from Scripts.neo_client import NeoClient

main_bp = Blueprint('main', __name__)

# Initialize components
trading_functions = TradingFunctions()
neo_client = NeoClient()


@main_bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    if session.get('authenticated'):
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/health')
def health():
    """Health check for webview accessibility"""
    return jsonify({
        'status': 'healthy',
        'message': 'Kotak Neo Trading Platform is running',
        'timestamp': datetime.now().isoformat()
    })


@main_bp.route('/test')
def test():
    """Simple test route for webview verification"""
    return '<h1>Kotak Neo Trading Platform</h1><p>Application is running successfully!</p>'


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with portfolio overview"""
    if not validate_current_session():
        if is_session_expired():
            flash('Your session has expired. Please login again.', 'warning')
        else:
            flash('Complete the 2FA process before accessing this application',
                  'error')
        session.clear()
        return redirect(url_for('auth.login') + '?expired=true')

    try:
        client = session.get('client')
        if not client:
            flash(
                'Session expired. Please complete the 2FA process and login again.',
                'error')
            session.clear()
            return redirect(url_for('auth.login'))

        # Try to validate session
        try:
            validation_result = neo_client.validate_session(client)
            if not validation_result:
                logging.warning(
                    "Session validation failed, but attempting to proceed with dashboard"
                )
        except Exception as val_error:
            logging.warning(
                f"Session validation error (proceeding): {val_error}")

        # Fetch dashboard data with error handling
        dashboard_data = {}
        try:
            raw_dashboard_data = trading_functions.get_dashboard_data(client)

            # Ensure dashboard_data is always a dictionary
            if isinstance(raw_dashboard_data, dict):
                dashboard_data = raw_dashboard_data
                # Validate that positions and holdings are lists
                if not isinstance(dashboard_data.get('positions'), list):
                    dashboard_data['positions'] = []
                if not isinstance(dashboard_data.get('holdings'), list):
                    dashboard_data['holdings'] = []
                if not isinstance(dashboard_data.get('limits'), dict):
                    dashboard_data['limits'] = {}
                if not isinstance(dashboard_data.get('recent_orders'), list):
                    dashboard_data['recent_orders'] = []
            elif isinstance(raw_dashboard_data, list):
                # If API returns a list directly, wrap it properly
                dashboard_data = {
                    'positions': raw_dashboard_data,
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': len(raw_dashboard_data),
                    'total_holdings': 0,
                    'total_orders': 0
                }
            else:
                # Fallback empty structure
                dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': 0,
                    'total_holdings': 0,
                    'total_orders': 0
                }

            # Ensure all required keys exist with default values and validate data types
            dashboard_data.setdefault('positions', [])
            dashboard_data.setdefault('holdings', [])
            dashboard_data.setdefault('limits', {})
            dashboard_data.setdefault('recent_orders', [])

            # Convert any non-list items to empty lists for safety
            if not isinstance(dashboard_data['positions'], list):
                dashboard_data['positions'] = []
            if not isinstance(dashboard_data['holdings'], list):
                dashboard_data['holdings'] = []
            if not isinstance(dashboard_data['recent_orders'], list):
                dashboard_data['recent_orders'] = []

            dashboard_data.setdefault('total_positions',
                                      len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings',
                                      len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders',
                                      len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            # Check if it's a 2FA error specifically
            if any(phrase in str(dashboard_error) for phrase in [
                    "Complete the 2fa process", "Invalid Credentials",
                    "Invalid JWT token"
            ]):
                flash(
                    'Complete the 2FA process before accessing this application',
                    'error')
                session.clear()
                return redirect(url_for('auth.login'))
            else:
                # For other errors, show dashboard with empty data
                flash(f'Some data could not be loaded: {str(dashboard_error)}',
                      'warning')
                dashboard_data = {
                    'positions': [],
                    'holdings': [],
                    'limits': {},
                    'recent_orders': [],
                    'total_positions': 0,
                    'total_holdings': 0,
                    'total_orders': 0
                }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        if "Complete the 2fa process" in str(
                e) or "Invalid Credentials" in str(e):
            flash('Complete the 2FA process before accessing this application',
                  'error')
            session.clear()
            return redirect(url_for('auth.login'))
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', data={})


@main_bp.route('/positions')
@login_required
def positions():
    """Positions page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        positions_data = trading_functions.get_positions(client)

        # Log the actual data structure for debugging
        if positions_data:
            if isinstance(positions_data, list) and len(positions_data) > 0:
                logging.info(
                    f"Positions data type: {type(positions_data)}, count: {len(positions_data)}"
                )
                logging.info(
                    f"First position keys: {list(positions_data[0].keys()) if positions_data[0] else 'Empty position'}"
                )
                logging.info(
                    f"Sample position data: {positions_data[0] if positions_data[0] else 'Empty'}"
                )
            elif isinstance(positions_data, dict):
                logging.info(f"Positions returned as dict: {positions_data}")
                if 'error' in positions_data:
                    flash(
                        f'Error loading positions: {positions_data["error"]}',
                        'error')
                    return render_template('positions.html', positions=[])
        else:
            logging.info("No positions data returned")

        # Ensure positions_data is always a list
        if not isinstance(positions_data, list):
            positions_data = []

        return render_template('positions.html', positions=positions_data)
    except Exception as e:
        logging.error(f"Positions error: {str(e)}")
        flash(f'Error loading positions: {str(e)}', 'error')
        return render_template('positions.html', positions=[])


@main_bp.route('/api/positions')
@login_required
def api_positions():
    """API endpoint for positions data (for AJAX refresh)"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        # Get fresh positions data
        positions_data = trading_functions.get_positions(client)

        # Handle error responses
        if isinstance(positions_data, dict) and 'error' in positions_data:
            error_message = positions_data['error']
            logging.error(f"Positions API returned error: {error_message}")
            return jsonify({
                'success': False,
                'message': error_message,
                'error': error_message,
                'positions': []
            }), 200  # Changed to 200 to avoid JS error handling issues

        # Ensure positions_data is a list
        if not isinstance(positions_data, list):
            logging.warning(
                f"Positions data is not a list, type: {type(positions_data)}")
            positions_data = []

        # Calculate summary statistics
        total_pnl = 0.0
        realized_pnl = 0.0
        unrealized_pnl = 0.0
        long_positions = 0
        short_positions = 0

        if positions_data:
            for position in positions_data:
                # Calculate P&L
                pnl = 0.0
                if position.get('urPnl'):
                    pnl = float(position.get('urPnl', 0))
                elif position.get('pnl'):
                    pnl = float(position.get('pnl', 0))
                elif position.get('rpnl'):
                    pnl = float(position.get('rpnl', 0))

                total_pnl += pnl

                # Calculate realized/unrealized P&L
                if position.get('rlPnl'):
                    realized_pnl += float(position.get('rlPnl', 0))
                if position.get('urPnl'):
                    unrealized_pnl += float(position.get('urPnl', 0))

                # Count long/short positions
                buy_qty = float(
                    position.get('flBuyQty', 0) or position.get('buyQty', 0)
                    or 0)
                sell_qty = float(
                    position.get('flSellQty', 0) or position.get('sellQty', 0)
                    or 0)
                net_qty = buy_qty - sell_qty

                if net_qty > 0:
                    long_positions += 1
                elif net_qty < 0:
                    short_positions += 1

        response_data = {
            'success': True,
            'positions': positions_data,
            'total_positions': len(positions_data) if positions_data else 0,
            'summary': {
                'total_pnl': total_pnl,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'long_positions': long_positions,
                'short_positions': short_positions
            },
            'timestamp': int(time.time())
        }

        logging.info(
            f"Returning positions API response: success={response_data['success']}, positions_count={len(positions_data)}"
        )
        return jsonify(response_data)
    except Exception as e:
        error_message = str(e)
        logging.error(f"API positions error: {error_message}")
        logging.error(f"Error type: {type(e).__name__}")

        # Check for specific error types
        if 'timeout' in error_message.lower():
            error_message = "Request timeout - please try again"
        elif 'connection' in error_message.lower():
            error_message = "Connection error - please check your internet connection"
        elif '2fa' in error_message.lower():
            error_message = "Authentication required - please login again"

        return jsonify({
            'success': False,
            'message': error_message,
            'error': str(e),
            'positions': []
        }), 500


@main_bp.route('/api/user_profile')
@login_required
def api_user_profile():
    """API endpoint for user profile"""
    try:
        # Get login time from session or format current time
        login_time = session.get('login_time', 'N/A')
        if login_time == 'N/A' or not login_time:
            from datetime import datetime
            login_time = datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')

        # Return comprehensive user session info
        profile_data = {
            'greeting_name':
            session.get('greeting_name', session.get('user_name', 'User')),
            'ucc':
            session.get('ucc', 'N/A'),
            'user_id':
            session.get('user_id', 'N/A'),
            'client_code':
            session.get('client_code', 'N/A'),
            'mobile_number':
            session.get('mobile_number', 'N/A'),
            'login_time':
            login_time,
            'access_token':
            session.get('access_token', 'N/A')[:20] +
            '...' if session.get('access_token') else 'N/A',
            'session_token':
            session.get('session_token', 'N/A')[:20] +
            '...' if session.get('session_token') else 'N/A',
            'sid':
            session.get('sid', 'N/A'),
            'rid':
            session.get('rid', 'N/A'),
            'token_status':
            'Valid' if session.get('authenticated') else 'Invalid',
            'authenticated':
            session.get('authenticated', False),
            'needs_reauth':
            not session.get('authenticated', False),
            'is_trial_account':
            session.get('is_trial_account', False),
            'account_type':
            session.get('account_type', 'Regular'),
            'branch_code':
            session.get('branch_code', 'N/A'),
            'product_code':
            session.get('product_code', 'N/A')
        }

        return jsonify({'success': True, 'profile': profile_data})

    except Exception as e:
        logging.error(f"User profile API error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/holdings')
@login_required
def holdings():
    """Holdings page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        holdings_data = trading_functions.get_holdings(client)
        return render_template('holdings.html', holdings=holdings_data)
    except Exception as e:
        logging.error(f"Holdings error: {str(e)}")
        flash(f'Error loading holdings: {str(e)}', 'error')
        return render_template('holdings.html', holdings=[])


@main_bp.route('/api/holdings')
@login_required
def api_holdings():
    """API endpoint for holdings data (for AJAX refresh)"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        # Get fresh holdings data
        holdings_data = trading_functions.get_holdings(client)

        # Handle error responses
        if isinstance(holdings_data, dict) and 'error' in holdings_data:
            error_message = holdings_data['error']
            logging.error(f"Holdings API returned error: {error_message}")
            return jsonify({
                'success': False,
                'message': error_message,
                'error': error_message,
                'holdings': []
            }), 400

        # Ensure holdings_data is a list
        if not isinstance(holdings_data, list):
            holdings_data = []

        # Calculate summary statistics
        total_invested = 0.0
        current_value = 0.0
        total_holdings = len(holdings_data)

        if holdings_data:
            for holding in holdings_data:
                # Calculate invested value
                invested = float(holding.get('holdingCost', 0) or 0)
                total_invested += invested

                # Calculate current market value
                market_val = float(holding.get('mktValue', 0) or 0)
                current_value += market_val

        return jsonify({
            'success': True,
            'holdings': holdings_data,
            'summary': {
                'total_holdings': total_holdings,
                'total_invested': total_invested,
                'current_value': current_value,
                'total_pnl': current_value - total_invested
            },
            'timestamp': int(time.time())
        })

    except Exception as e:
        error_message = str(e)
        logging.error(f"API holdings error: {error_message}")
        logging.error(f"Error type: {type(e).__name__}")

        # Check for specific error types
        if 'timeout' in error_message.lower():
            error_message = "Request timeout - please try again"
        elif 'connection' in error_message.lower():
            error_message = "Connection error - please check your internet connection"
        elif '2fa' in error_message.lower():
            error_message = "Authentication required - please login again"

        return jsonify({
            'success': False,
            'message': error_message,
            'error': str(e),
            'holdings': []
        }), 500


@main_bp.route('/orders')
@login_required
def orders():
    """Orders page"""
    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('auth.login'))

        orders_data = trading_functions.get_orders(client)
        return render_template('orders.html', orders=orders_data)
    except Exception as e:
        logging.error(f"Orders error: {str(e)}")
        flash(f'Error loading orders: {str(e)}', 'error')
        return render_template('orders.html', orders=[])


@main_bp.route('/api/orders')
@login_required
def api_orders():
    """API endpoint for orders data (for AJAX refresh)"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        orders_data = trading_functions.get_orders(client)
        return jsonify({
            'success': True,
            'orders': orders_data,
            'total_orders': len(orders_data) if orders_data else 0
        })
    except Exception as e:
        logging.error(f"API orders error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'orders': []
        }), 500


@main_bp.route('/charts')
@login_required
def charts():
    """Charts page with Dash integration"""
    try:
        # Check if Dash app is available
        from dash_charts_app import dash_app
        # Redirect to Dash app
        return render_template('charts.html', dash_url='/dash-charts/')
    except ImportError:
        # Fallback to basic charts page
        return render_template('charts.html', dash_url=None)


@main_bp.route('/portfolio')
@login_required
def portfolio():
    """Portfolio page with trading signals overview"""
    return render_template('portfolio.html')


@main_bp.route('/etf-signals')
@login_required
def etf_signals():
    """ETF Signals page"""
    return render_template('etf_signals.html')

@main_bp.route('/deals')
@login_required
def deals():
    """Deals page for placed orders from signals"""
    return render_template('deals.html')


@main_bp.route('/default-deals')
@login_required
def default_deals():
    """Default deals page showing all deals"""
    return render_template('default_deals.html')


@main_bp.route('/api/deals/user', methods=['GET'])
def api_get_user_deals():
    """API endpoint for getting user deals - redirect to deals API"""
    try:
        from api.deals_api import get_user_deals_api
        return get_user_deals_api()
    except Exception as e:
        logging.error(f"Error in user deals API: {e}")
        return jsonify({
            'success': False,
            'deals': [],
            'total': 0,
            'error': str(e)
        }), 500


@main_bp.route('/api/deals/create-from-signal', methods=['POST'])
def api_create_deal_from_signal():
    """API endpoint for creating a deal from a signal"""
    try:
        logging.info("Create deal from signal endpoint called")

        data = request.get_json()
        logging.info(f"Received data: {data}")

        if not data or 'signal_data' not in data:
            logging.error("No signal data provided in request")
            return jsonify({
                'success': False,
                'message': 'No signal data provided'
            }), 400

        signal_data = data['signal_data']
        logging.info(f"Signal data: {signal_data}")

        # Extract signal information with better error handling
        try:
            symbol = signal_data.get('symbol') or signal_data.get(
                'etf', 'UNKNOWN')
            qty = int(signal_data.get('qty', 1))
            ep = float(signal_data.get('ep', 0))
            cmp = float(signal_data.get('cmp', ep))
            pos = int(signal_data.get('pos', 1))
            inv = float(signal_data.get('inv', ep * qty))
            tp = float(signal_data.get('tp', ep * 1.05))

            # Validate required data
            if not symbol or symbol == 'UNKNOWN':
                raise ValueError("Invalid symbol")
            if ep <= 0:
                raise ValueError("Invalid entry price")
            if qty <= 0:
                raise ValueError("Invalid quantity")

        except (ValueError, TypeError) as e:
            logging.error(f"Error parsing signal data: {e}")
            return jsonify({
                'success': False,
                'message': f'Invalid signal data format: {str(e)}'
            }), 400

        logging.info(
            f"Parsed signal - Symbol: {symbol}, Qty: {qty}, EP: {ep}, CMP: {cmp}"
        )

        # Use the existing models to create a user deal
        try:
            from core.database import get_db_connection
            import psycopg2.extras

            # Get database connection
            conn = get_db_connection()
            if not conn:
                raise Exception("Failed to connect to database")

            # Calculate current value and PnL
            current_value = cmp * qty
            pnl_amount = current_value - inv
            pnl_percent = (pnl_amount / inv * 100) if inv > 0 else 0

            with conn.cursor() as cursor:
                # Insert new deal into user_deals table
                insert_query = """
                    INSERT INTO user_deals (
                        symbol, entry_date, position_type, quantity, entry_price, 
                        current_price, target_price, invested_amount, current_value,
                        pnl_amount, pnl_percent, status, deal_type, notes,
                        pos, qty, ep, cmp, tp, inv, pl, chan_percent,
                        signal_date, thirty, dh, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, tva, tpr,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """

                cursor.execute(
                    insert_query,
                    (symbol.upper(), signal_data.get('date', 'CURRENT_DATE'),
                     'LONG' if pos == 1 else 'SHORT', qty, ep, cmp, tp, inv,
                     current_value, pnl_amount, pnl_percent, 'ACTIVE',
                     'SIGNAL', f'Added from ETF signal - {symbol}', pos, qty,
                     ep, cmp, tp, inv, pnl_amount, f"{pnl_percent:.2f}%",
                     signal_data.get('date', ''),
                     signal_data.get('thirty', '0%'), signal_data.get('dh', 0),
                     signal_data.get('ed', ''), signal_data.get('exp', ''),
                     signal_data.get('pr', ''), signal_data.get('pp', ''),
                     signal_data.get('iv', ''), signal_data.get('ip', ''),
                     signal_data.get('nt', f'Signal for {symbol}'),
                     signal_data.get('qt', ''), signal_data.get(
                         'seven', '0%'), signal_data.get('ch', '0%'),
                     signal_data.get('tva', current_value),
                     signal_data.get('tpr', pnl_amount), 'NOW()'))

                deal_id = cursor.fetchone()[0]
                conn.commit()

            logging.info(
                f"✓ Created deal from signal: {symbol} - Deal ID: {deal_id}")

            return jsonify({
                'success': True,
                'message': f'Deal created successfully for {symbol}',
                'deal_id': deal_id,
                'symbol': symbol,
                'entry_price': ep,
                'quantity': qty
            })

        except Exception as model_error:
            logging.error(f"Model error creating deal: {model_error}")
            if conn:
                conn.rollback()
            return jsonify({
                'success':
                False,
                'message':
                f'Failed to create deal: {str(model_error)}'
            }), 500
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logging.error(f"Error creating deal from signal: {e}")
        return jsonify({
            'success': False,
            'message': f'Error creating deal: {str(e)}'
        }), 500


@main_bp.route('/admin')
@login_required
def admin_panel():
    """Admin panel for trade signal management"""
    try:
        return render_template('admin_panel.html')
    except Exception as e:
        logging.error(f"Admin panel error: {str(e)}")
        flash('Error loading admin panel', 'error')
        return redirect(url_for('main.dashboard'))

# Trading Signals page route
@main_bp.route('/trading-signals')
@login_required
def trading_signals():
    """Trading signals page"""
    return render_template('trading_signals.html')