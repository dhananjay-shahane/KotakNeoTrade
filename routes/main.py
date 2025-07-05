"""Main application routes"""
from flask import Blueprint, render_template, session, flash, redirect, url_for, jsonify
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
            flash('Complete the 2FA process before accessing this application', 'error')
        session.clear()
        return redirect(url_for('auth.login') + '?expired=true')

    try:
        client = session.get('client')
        if not client:
            flash('Session expired. Please complete the 2FA process and login again.', 'error')
            session.clear()
            return redirect(url_for('auth.login'))

        # Try to validate session
        try:
            validation_result = neo_client.validate_session(client)
            if not validation_result:
                logging.warning("Session validation failed, but attempting to proceed with dashboard")
        except Exception as val_error:
            logging.warning(f"Session validation error (proceeding): {val_error}")

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

            dashboard_data.setdefault('total_positions', len(dashboard_data['positions']))
            dashboard_data.setdefault('total_holdings', len(dashboard_data['holdings']))
            dashboard_data.setdefault('total_orders', len(dashboard_data['recent_orders']))

        except Exception as dashboard_error:
            logging.error(f"Dashboard data fetch failed: {dashboard_error}")
            # Check if it's a 2FA error specifically
            if any(phrase in str(dashboard_error) for phrase in [
                "Complete the 2fa process", 
                "Invalid Credentials", 
                "Invalid JWT token"
            ]):
                flash('Complete the 2FA process before accessing this application', 'error')
                session.clear()
                return redirect(url_for('auth.login'))
            else:
                # For other errors, show dashboard with empty data
                flash(f'Some data could not be loaded: {str(dashboard_error)}', 'warning')
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
        if "Complete the 2fa process" in str(e) or "Invalid Credentials" in str(e):
            flash('Complete the 2FA process before accessing this application', 'error')
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
                logging.info(f"Positions data type: {type(positions_data)}, count: {len(positions_data)}")
                logging.info(f"First position keys: {list(positions_data[0].keys()) if positions_data[0] else 'Empty position'}")
                logging.info(f"Sample position data: {positions_data[0] if positions_data[0] else 'Empty'}")
            elif isinstance(positions_data, dict):
                logging.info(f"Positions returned as dict: {positions_data}")
                if 'error' in positions_data:
                    flash(f'Error loading positions: {positions_data["error"]}', 'error')
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
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

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
            logging.warning(f"Positions data is not a list, type: {type(positions_data)}")
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
                buy_qty = float(position.get('flBuyQty', 0) or position.get('buyQty', 0) or 0)
                sell_qty = float(position.get('flSellQty', 0) or position.get('sellQty', 0) or 0)
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

        logging.info(f"Returning positions API response: success={response_data['success']}, positions_count={len(positions_data)}")
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

@main_bp.route('/api/portfolio_summary')
@login_required
def api_portfolio_summary():
    """API endpoint for portfolio summary data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

        # Get dashboard data
        dashboard_data = trading_functions.get_dashboard_data(client)

        if not dashboard_data or not isinstance(dashboard_data, dict):
            return jsonify({'success': False, 'message': 'Failed to fetch dashboard data.'}), 500

        # Calculate summary statistics
        limits_data = dashboard_data.get('limits', {})
        portfolio_summary = {
            'total_positions': dashboard_data.get('total_positions', 0),
            'total_holdings': dashboard_data.get('total_holdings', 0),
            'total_orders': dashboard_data.get('total_orders', 0),
            'limits_available': float(limits_data.get('Net', 0) or 0),
            'margin_used': float(limits_data.get('MarginUsed', 0) or 0),
            'collateral_value': float(limits_data.get('CollateralValue', 0) or 0),
            'total_pnl': 0.0,
            'total_investment': 0.0
        }

        # Calculate P&L from positions
        positions = dashboard_data.get('positions', [])
        for position in positions:
            try:
                pnl = float(position.get('pnl', 0) or 0)
                portfolio_summary['total_pnl'] += pnl
            except (ValueError, TypeError):
                continue

        # Calculate investment from holdings
        holdings = dashboard_data.get('holdings', [])
        for holding in holdings:
            try:
                quantity = float(holding.get('quantity', 0) or 0)
                avg_price = float(holding.get('avgPrice', 0) or 0)
                portfolio_summary['total_investment'] += quantity * avg_price
            except (ValueError, TypeError):
                continue

        return jsonify({
            'success': True,
            **portfolio_summary
        })

    except Exception as e:
        logging.error(f"Portfolio summary API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@main_bp.route('/api/portfolio_details')
@login_required
def api_portfolio_details():
    """API endpoint for detailed portfolio data"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

        portfolio_data = trading_functions.get_portfolio_summary(client)
        return jsonify(portfolio_data)

    except Exception as e:
        logging.error(f"Portfolio details API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main_bp.route('/api/live_quotes')
@login_required
def api_live_quotes():
    """API endpoint for live quotes"""
    try:
        # Return sample quotes for now - you can implement actual quote fetching
        # sample_quotes = [
        #     {'symbol': 'RELIANCE', 'ltp': 2890.50, 'changePct': 1.2},
        #     {'symbol': 'TCS', 'ltp': 3456.75, 'changePct': -0.8},
        #     {'symbol': 'HDFC', 'ltp': 1789.25, 'changePct': 0.5},
        #     {'symbol': 'INFY', 'ltp': 1523.80, 'changePct': 2.1}
        # ]

        return jsonify({
            'success': True,
            # 'quotes': sample_quotes
        })

    except Exception as e:
        logging.error(f"Live quotes API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'quotes': []
        }), 500

@main_bp.route('/etf-signals')
@login_required
def etf_signals():
    """ETF Signals page - show admin_trade_signals data from external database"""
    try:
        # Get signals count from external database
        from Scripts.external_db_service import get_etf_signals_from_external_db
        
        try:
            signals = get_etf_signals_from_external_db()
            signals_count = len(signals) if signals else 0
        except Exception as e:
            logging.error(f"Error fetching signals from external DB: {str(e)}")
            signals_count = 0

        logging.info(f"ETF Signals page: Displaying {signals_count} admin trade signals in datatable")

        return render_template('etf_signals.html', signals_count=signals_count)

    except Exception as e:
        logging.error(f"ETF signals page error: {str(e)}")
        flash(f'Error loading ETF signals page: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/api/etf_positions')
@login_required
def api_etf_positions():
    """API endpoint for ETF positions"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get current user from database
        from Scripts.models import User
        current_user = User.query.get(session['user_id'])
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get ETF signal trades for current user
        from Scripts.models_etf import ETFSignalTrade
        trades = ETFSignalTrade.query.filter_by(user_id=current_user.id).order_by(ETFSignalTrade.created_at.desc()).all()

        # Calculate portfolio summary
        total_invested = 0
        current_value = 0
        total_pnl = 0
        profit_trades = 0
        loss_trades = 0

        trades_data = []
        for trade in trades:
            trade_dict = trade.to_dict()
            trades_data.append(trade_dict)

            # Update calculations
            if trade.invested_amount:
                total_invested += float(trade.invested_amount)
            if trade.current_value:
                current_value += float(trade.current_value)
            if trade.pnl_amount:
                pnl = float(trade.pnl_amount)
                total_pnl += pnl
                if pnl > 0:
                    profit_trades += 1
                elif pnl < 0:
                    loss_trades += 1

        # Calculate return percentage
        return_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        portfolio_summary = {
            'total_invested': total_invested,
            'current_value': current_value,
            'total_pnl': total_pnl,
            'return_percent': return_percent,
            'profit_trades': profit_trades,
            'loss_trades': loss_trades,
            'total_trades': len(trades_data)
        }

        return jsonify({
            'success': True,
            'trades': trades_data,
            'portfolio': portfolio_summary
        })

    except Exception as e:
        logging.error(f"Error fetching ETF positions: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching data: {str(e)}'}), 500

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
            'greeting_name': session.get('greeting_name', session.get('user_name', 'User')),
            'ucc': session.get('ucc', 'N/A'),
            'user_id': session.get('user_id', 'N/A'),
            'client_code': session.get('client_code', 'N/A'),
            'mobile_number': session.get('mobile_number', 'N/A'),
            'login_time': login_time,
            'access_token': session.get('access_token', 'N/A')[:20] + '...' if session.get('access_token') else 'N/A',
            'session_token': session.get('session_token', 'N/A')[:20] + '...' if session.get('session_token') else 'N/A',
            'sid': session.get('sid', 'N/A'),
            'rid': session.get('rid', 'N/A'),
            'token_status': 'Valid' if session.get('authenticated') else 'Invalid',
            'authenticated': session.get('authenticated', False),
            'needs_reauth': not session.get('authenticated', False),
            'is_trial_account': session.get('is_trial_account', False),
            'account_type': session.get('account_type', 'Regular'),
            'branch_code': session.get('branch_code', 'N/A'),
            'product_code': session.get('product_code', 'N/A')
        }

        return jsonify({
            'success': True,
            'profile': profile_data
        })

    except Exception as e:
        logging.error(f"User profile API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

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
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

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
    """Charts page for trading analysis"""
    return render_template('charts.html')

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

# @main_bp.route('/api/etf-signals-data')
# @login_required
# def api_etf_signals_data():
#     """API endpoint for ETF signals data"""
#     try:
#         from sqlalchemy import text
#         from app import db

#         # Use raw SQL to get signals data with only existing columns
#         result = db.session.execute(text("""
#             SELECT id, symbol, entry_price, current_price, quantity, investment_amount, 
#                    signal_type, status, created_at, pnl, pnl_percentage, change_percent,
#                    target_price, stop_loss, last_update_time
#             FROM admin_trade_signals 
#             ORDER BY created_at DESC
#             LIMIT 100
#         """))

#         signals_data = result.fetchall()

#         # Format data for frontend
#         formatted_signals = []
#         for row in signals_data:
#             signal = {
#                 'id': row[0],
#                 'trade_signal_id': row[0],
#                 'etf': row[1] or 'N/A',
#                 'symbol': row[1] or 'N/A',
#                 'thirty': '30',
#                 'dh': '0',
#                 'date': row[8].strftime('%Y-%m-%d') if row[8] else '',
#                 'pos': 1 if row[2] == 'BUY' else -1,
#                 'qty': row[6] or 1,
#                 'ep': float(row[3]) if row[3] else 0,
#                 'cmp': float(row[4]) if row[4] else 0,
#                 'chan': f"{float(row[12]):.2f}%" if row[12] else "0%",
#                 'inv': float(row[9]) if row[9] else 0,
#                 'tp': float(row[5]) if row[5] else 0,
#                 'tva': 0,
#                 'tpr': 0,
#                 'pl': float(row[10]) if row[10] else 0,
#                 'ed': row[8].strftime('%Y-%m-%d') if row[8] else '',
#                 'exp': '',
#                 'pr': '',
#                 'pp': f"{float(row[11]):.2f}%" if row[11] else "0%",
#                 'iv': '',
#                 'ip': '',
#                 'nt': '',
#                 'qt': '',
#                 'seven': '0',
#                 'ch': f"{float(row[12]):.2f}%" if row[12] else "0%",
#                 'status': row[7] or 'ACTIVE'
#             }
#             formatted_signals.append(signal)

#         return jsonify({
#             'success': True,
#             'data': formatted_signals,
#             'total': len(formatted_signals)
#         })

#     except Exception as e:
#         logging.error(f"ETF signals data API error: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'data': [],
#             'total': 0
#         }), 500

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