"""
API Routes Functions
Contains all API endpoint functions
"""
from flask import request, jsonify, session, redirect, url_for
import logging
import os

def get_dashboard_data_api(trading_functions):
    """AJAX endpoint for dashboard data without page refresh"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        dashboard_data = trading_functions.get_dashboard_data(client)
        return jsonify(dashboard_data)

    except Exception as e:
        logging.error(f"Dashboard API error: {e}")
        return jsonify({'error': str(e)}), 500

def get_holdings_api(trading_functions):
    """API endpoint to get holdings"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        holdings_data = trading_functions.get_holdings(client)
        return jsonify(holdings_data)

    except Exception as e:
        logging.error(f"Holdings API error: {e}")
        return jsonify({'error': str(e)}), 500

def get_etf_signals_data():
    """API endpoint to get ETF signals data from external admin_trade_signals table"""
    try:
        from Scripts.external_db_service import get_etf_signals_data_json
        return get_etf_signals_data_json()
    except Exception as e:
        logging.error(f"ETF signals API error: {e}")
        return jsonify({'error': str(e)}), 500

def place_order(neo_client):
    """API endpoint to place buy/sell orders using Kotak Neo API"""
    try:
        # Get form data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['exchange_segment', 'product', 'price', 'order_type', 'quantity', 'validity', 'trading_symbol', 'transaction_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Get client from session
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

        # Execute order placement
        result = neo_client.place_order(
            client=client,
            exchange_segment=data['exchange_segment'],
            product=data['product'],
            price=data['price'],
            order_type=data['order_type'],
            quantity=data['quantity'],
            validity=data['validity'],
            trading_symbol=data['trading_symbol'],
            transaction_type=data['transaction_type'],
            amo=data.get('amo', 'NO'),
            disclosed_quantity=data.get('disclosed_quantity', '0'),
            market_protection=data.get('market_protection', '0'),
            pf=data.get('pf', 'N'),
            trigger_price=data.get('trigger_price', '0'),
            tag=data.get('tag', None)
        )

        if result and result.get('stat') == 'Ok':
            return jsonify({
                'success': True,
                'message': 'Order placed successfully!',
                'data': result.get('data', {})
            })
        else:
            error_msg = result.get('emsg', 'Order placement failed') if result else 'Unknown error'
            return jsonify({
                'success': False,
                'message': f'Order failed: {error_msg}'
            }), 400

    except Exception as e:
        logging.error(f"Place order error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error placing order: {str(e)}'
        }), 500

def health_check():
    """Health check endpoint for domain verification"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat()
    })

def test_endpoint():
    """Test endpoint for DNS verification"""
    return jsonify({
        'message': 'Test endpoint working', 
        'timestamp': datetime.now().isoformat()
    })

def preview_test():
    """Simple preview test page"""
    return '<h1>Kotak Neo Trading Platform</h1><p>Application is running successfully!</p>'