from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime

# Create the trading blueprint
trading_bp = Blueprint('trading_api', __name__, url_prefix='/api/trading')

# Export as trading_api for compatibility with existing imports
trading_api = trading_bp

@trading_bp.route('/place_order', methods=['POST'])
def place_order():
    """Place a trading order using the provided parameters"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Get the trading client from session
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Trading client not available. Please login again.'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Extract order parameters exactly as specified in client.place_order
        exchange_segment = data.get('exchange_segment', 'nse_cm')
        product = data.get('product', 'CNC')
        price = data.get('price', '0')
        order_type = data.get('order_type', 'MKT')
        quantity = data.get('quantity', '1')
        validity = data.get('validity', 'DAY')
        trading_symbol = data.get('trading_symbol', '')
        transaction_type = data.get('transaction_type', 'BUY')
        amo = data.get('amo', 'NO')
        disclosed_quantity = data.get('disclosed_quantity', '0')
        market_protection = data.get('market_protection', '0')
        pf = data.get('pf', 'N')
        trigger_price = data.get('trigger_price', '0')
        tag = data.get('tag', None)

        # Validate required fields
        if not trading_symbol or not quantity:
            return jsonify({'success': False, 'message': 'Trading symbol and quantity are required'}), 400

        # Log the order attempt
        logging.info(f"Place order request: {transaction_type} {quantity} {trading_symbol} at {price} ({order_type}) from {tag}")

        # Place order using the exact client.place_order API structure
        order_response = client.place_order(
            exchange_segment=exchange_segment,
            product=product,
            price=price,
            order_type=order_type,
            quantity=quantity,
            validity=validity,
            trading_symbol=trading_symbol,
            transaction_type=transaction_type,
            amo=amo,
            disclosed_quantity=disclosed_quantity,
            market_protection=market_protection,
            pf=pf,
            trigger_price=trigger_price,
            tag=tag
        )

        # Process the response from the trading client
        if order_response and 'stat' in order_response:
            if order_response['stat'] == 'Ok':
                order_id = order_response.get('nOrdNo', f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                response_data = {
                    'success': True,
                    'message': f'{transaction_type} order for {quantity} {trading_symbol} placed successfully',
                    'order_id': order_id,
                    'order_details': {
                        'symbol': trading_symbol,
                        'quantity': int(quantity),
                        'price': float(price) if price != '0' else 'Market Price',
                        'order_type': order_type,
                        'transaction_type': transaction_type,
                        'product': product,
                        'validity': validity,
                        'exchange': exchange_segment,
                        'timestamp': datetime.now().isoformat(),
                        'tag': tag
                    },
                    'raw_response': order_response
                }
                
                logging.info(f"Order placed successfully: {order_id}")
                return jsonify(response_data)
            else:
                error_msg = order_response.get('emsg', 'Unknown error from trading client')
                logging.error(f"Order placement failed: {error_msg}")
                return jsonify({
                    'success': False, 
                    'message': f'Order placement failed: {error_msg}',
                    'raw_response': order_response
                }), 400
        else:
            logging.error(f"Invalid response from trading client: {order_response}")
            return jsonify({
                'success': False, 
                'message': 'Invalid response from trading client',
                'raw_response': order_response
            }), 500

    except Exception as e:
        logging.error(f"Error placing order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error placing order: {str(e)}'}), 500

@trading_bp.route('/get_positions', methods=['GET'])
def get_positions():
    """Get user positions"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Mock positions data
        positions = []

        return jsonify({
            'success': True,
            'positions': positions,
            'message': 'Positions retrieved successfully'
        })

    except Exception as e:
        logging.error(f"Error getting positions: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting positions: {str(e)}'}), 500

@trading_bp.route('/get_orders', methods=['GET'])
def get_orders():
    """Get user orders"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401

        # Mock orders data
        orders = []

        return jsonify({
            'success': True,
            'orders': orders,
            'message': 'Orders retrieved successfully'
        })

    except Exception as e:
        logging.error(f"Error getting orders: {str(e)}")
        return jsonify({'success': False, 'message': f'Error getting orders: {str(e)}'}), 500

@trading_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for trading API"""
    return jsonify({
        'success': True,
        'message': 'Trading API is running',
        'timestamp': datetime.now().isoformat()
    })