"""
Trading API endpoints for Kotak Neo Trading Platform
Handles order placement, trading operations, and portfolio management
"""
import logging
from flask import Blueprint, jsonify, session, request
from Scripts.trading_functions import TradingFunctions
from Scripts.neo_client import NeoClient

# Create blueprint for trading API
trading_bp = Blueprint('trading_api', __name__, url_prefix='/api')

# Initialize components
trading_functions = TradingFunctions()
neo_client = NeoClient()


def require_auth():
    """Check if user is authenticated"""
    return session.get('client') is not None


@trading_bp.route('/place-order', methods=['POST'])
def place_order():
    """API endpoint to place buy/sell orders using Kotak Neo API"""
    if not require_auth():
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401

    try:
        # Get order data from request
        order_data = request.get_json()

        # Validate required fields
        required_fields = [
            'symbol', 'quantity', 'transaction_type', 'order_type'
        ]
        for field in required_fields:
            if field not in order_data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400

        # Get client from session
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please login again.'
            }), 401

        # Validate session before placing order
        try:
            if not neo_client.validate_session(client):
                return jsonify({
                    'success': False,
                    'message': 'Trading session has expired. Please logout and login again to enable trading operations.'
                }), 401
        except Exception as e:
            logging.warning(f"Session validation failed: {e}")

        # Prepare order data with defaults
        order_params = {
            'symbol': order_data['symbol'],
            'quantity': str(order_data['quantity']),
            'transaction_type': order_data['transaction_type'],
            'order_type': order_data['order_type'],
            'exchange_segment': order_data.get('exchange_segment', 'nse_cm'),
            'product': order_data.get('product', 'CNC'),
            'validity': order_data.get('validity', 'DAY'),
            'price': order_data.get('price', '0'),
            'trigger_price': order_data.get('trigger_price', '0'),
            'disclosed_quantity': order_data.get('disclosed_quantity', '0'),
            'amo': order_data.get('amo', 'NO'),
            'market_protection': order_data.get('market_protection', '0'),
            'pf': order_data.get('pf', 'N'),
            'tag': order_data.get('tag', None)
        }

        # Place the order
        result = trading_functions.place_order(client, order_params)

        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Order placed successfully',
                'order_id': result.get('order_id'),
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Order placement failed'),
                'error': result.get('error', 'Unknown error')
            }), 400

    except Exception as e:
        logging.error(f"Order placement error: {e}")
        return jsonify({
            'success': False,
            'message': f'Order placement failed: {str(e)}'
        }), 500


@trading_bp.route('/quick-buy', methods=['POST'])
def quick_buy():
    """Quick buy order for holdings/default-deals pages"""
    if not require_auth():
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401

    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity', 1)

        if not symbol:
            return jsonify({
                'success': False,
                'message': 'Symbol is required'
            }), 400

        # Prepare quick buy order
        order_params = {
            'symbol': symbol,
            'quantity': str(quantity),
            'transaction_type': 'B',  # Buy
            'order_type': 'MARKET',
            'exchange_segment': 'nse_cm',
            'product': 'CNC',
            'validity': 'DAY',
            'price': '0',
            'trigger_price': '0'
        }

        client = session.get('client')
        result = trading_functions.place_order(client, order_params)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Quick buy error: {e}")
        return jsonify({
            'success': False,
            'message': f'Quick buy failed: {str(e)}'
        }), 500


@trading_bp.route('/quick-sell', methods=['POST'])
def quick_sell():
    """Quick sell order for holdings/default-deals pages"""
    if not require_auth():
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401

    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = data.get('quantity', 1)

        if not symbol:
            return jsonify({
                'success': False,
                'message': 'Symbol is required'
            }), 400

        # Prepare quick sell order
        order_params = {
            'symbol': symbol,
            'quantity': str(quantity),
            'transaction_type': 'S',  # Sell
            'order_type': 'MARKET',
            'exchange_segment': 'nse_cm',
            'product': 'CNC',
            'validity': 'DAY',
            'price': '0',
            'trigger_price': '0'
        }

        client = session.get('client')
        result = trading_functions.place_order(client, order_params)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Quick sell error: {e}")
        return jsonify({
            'success': False,
            'message': f'Quick sell failed: {str(e)}'
        }), 500


@trading_bp.route('/orders', methods=['GET'])
def get_orders_api():
    try:
        # Get orders data using the trading functions
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Not authenticated',
                'orders': []
            }), 401

        orders_data = trading_functions.get_orders(client)

        return jsonify({
            'success': True,
            'orders': orders_data or []
        })

    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'orders': []
        }), 500


@trading_bp.route('/holdings')
def get_holdings_api():
    try:
        # Get holdings data using the trading functions
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Not authenticated',
                'holdings': []
            }), 401

        holdings_data = trading_functions.get_holdings(client)

        return jsonify({
            'success': True,
            'holdings': holdings_data or []
        })

    except Exception as e:
        logging.error(f"Error fetching holdings: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'holdings': []
        }), 500


@trading_bp.route('/positions')
def get_positions_api():
    try:
        # Get positions data using the trading functions
        client = session.get('client')
        if not client:
            return jsonify({
                'success': False,
                'message': 'Not authenticated',
                'positions': []
            }), 401

        positions_data = trading_functions.get_positions(client)

        return jsonify({
            'success': True,
            'positions': positions_data or []
        })

    except Exception as e:
        logging.error(f"Error fetching positions: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'positions': []
        }), 500