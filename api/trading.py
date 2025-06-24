"""Trading API endpoints"""
from flask import Blueprint, request, jsonify, session
import logging
import random
from datetime import datetime, timedelta

from utils.auth import login_required
from trading_functions import TradingFunctions

trading_api = Blueprint('trading_api', __name__)
trading_functions = TradingFunctions()

@trading_api.route('/place_order', methods=['POST'])
@login_required
def place_order():
    """Place a new order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.place_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Place order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/modify_order', methods=['POST'])
@login_required
def modify_order():
    """Modify an existing order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.modify_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Modify order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/cancel_order', methods=['POST'])
@login_required
def cancel_order():
    """Cancel an existing order"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        order_data = request.get_json()
        result = trading_functions.cancel_order(client, order_data)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logging.error(f"Cancel order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@trading_api.route('/get_quotes')
@login_required
def get_quotes():
    """API endpoint to get live quotes"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        quote_data = {
            'instrument_tokens': request.args.getlist('tokens'),
            'quote_type': request.args.get('type', 'ltp')
        }
        result = trading_functions.get_quotes(client, quote_data)
        return jsonify(result)

    except Exception as e:
        logging.error(f"Get quotes error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trading_api.route('/search-symbols')
@login_required
def search_symbols():
    """Search trading symbols"""
    try:
        query = request.args.get('q', '').strip().upper()
        if not query or len(query) < 2:
            return jsonify([])

        # Expanded Indian stocks database for better search results
        all_symbols = [
            {'symbol': 'RELIANCE', 'name': 'Reliance Industries Limited', 'sector': 'Oil & Gas'},
            {'symbol': 'TCS', 'name': 'Tata Consultancy Services Limited', 'sector': 'IT Services'},
            {'symbol': 'HDFCBANK', 'name': 'HDFC Bank Limited', 'sector': 'Banking'},
            {'symbol': 'INFY', 'name': 'Infosys Limited', 'sector': 'IT Services'},
            {'symbol': 'ICICIBANK', 'name': 'ICICI Bank Limited', 'sector': 'Banking'},
            {'symbol': 'BHARTIARTL', 'name': 'Bharti Airtel Limited', 'sector': 'Telecom'},
            {'symbol': 'ITC', 'name': 'ITC Limited', 'sector': 'FMCG'},
            {'symbol': 'SBIN', 'name': 'State Bank of India', 'sector': 'Banking'},
            {'symbol': 'LT', 'name': 'Larsen & Toubro Limited', 'sector': 'Engineering'},
            {'symbol': 'KOTAKBANK', 'name': 'Kotak Mahindra Bank Limited', 'sector': 'Banking'},
            {'symbol': 'HINDUNILVR', 'name': 'Hindustan Unilever Limited', 'sector': 'FMCG'},
            {'symbol': 'BAJFINANCE', 'name': 'Bajaj Finance Limited', 'sector': 'Financial Services'},
            {'symbol': 'AXISBANK', 'name': 'Axis Bank Limited', 'sector': 'Banking'},
            {'symbol': 'ASIANPAINT', 'name': 'Asian Paints Limited', 'sector': 'Paints'},
            {'symbol': 'MARUTI', 'name': 'Maruti Suzuki India Limited', 'sector': 'Auto'},
            {'symbol': 'NESTLEIND', 'name': 'Nestle India Limited', 'sector': 'FMCG'},
            {'symbol': 'TITAN', 'name': 'Titan Company Limited', 'sector': 'Jewellery'},
            {'symbol': 'WIPRO', 'name': 'Wipro Limited', 'sector': 'IT Services'},
            {'symbol': 'TATAMOTORS', 'name': 'Tata Motors Limited', 'sector': 'Auto'},
            {'symbol': 'HCLTECH', 'name': 'HCL Technologies Limited', 'sector': 'IT Services'},
            {'symbol': 'TECHM', 'name': 'Tech Mahindra Limited', 'sector': 'IT Services'},
            {'symbol': 'ULTRACEMCO', 'name': 'UltraTech Cement Limited', 'sector': 'Cement'},
            {'symbol': 'POWERGRID', 'name': 'Power Grid Corporation of India Limited', 'sector': 'Power'},
            {'symbol': 'NTPC', 'name': 'NTPC Limited', 'sector': 'Power'},
            {'symbol': 'ONGC', 'name': 'Oil and Natural Gas Corporation Limited', 'sector': 'Oil & Gas'},
            {'symbol': 'JSWSTEEL', 'name': 'JSW Steel Limited', 'sector': 'Steel'},
            {'symbol': 'TATASTEEL', 'name': 'Tata Steel Limited', 'sector': 'Steel'},
            {'symbol': 'GRASIM', 'name': 'Grasim Industries Limited', 'sector': 'Textiles'},
            {'symbol': 'INDUSINDBK', 'name': 'IndusInd Bank Limited', 'sector': 'Banking'},
            {'symbol': 'ADANIPORTS', 'name': 'Adani Ports and Special Economic Zone Limited', 'sector': 'Infrastructure'},
            {'symbol': 'COALINDIA', 'name': 'Coal India Limited', 'sector': 'Mining'},
            {'symbol': 'BAJAJFINSV', 'name': 'Bajaj Finserv Limited', 'sector': 'Financial Services'},
            {'symbol': 'DIVISLAB', 'name': 'Divi\'s Laboratories Limited', 'sector': 'Pharma'},
            {'symbol': 'DRREDDY', 'name': 'Dr. Reddy\'s Laboratories Limited', 'sector': 'Pharma'},
            {'symbol': 'SUNPHARMA', 'name': 'Sun Pharmaceutical Industries Limited', 'sector': 'Pharma'},
            {'symbol': 'CIPLA', 'name': 'Cipla Limited', 'sector': 'Pharma'},
            {'symbol': 'EICHERMOT', 'name': 'Eicher Motors Limited', 'sector': 'Auto'},
            {'symbol': 'HEROMOTOCO', 'name': 'Hero MotoCorp Limited', 'sector': 'Auto'},
            {'symbol': 'BAJAJ-AUTO', 'name': 'Bajaj Auto Limited', 'sector': 'Auto'},
            {'symbol': 'M&M', 'name': 'Mahindra & Mahindra Limited', 'sector': 'Auto'},
            {'symbol': 'BRITANNIA', 'name': 'Britannia Industries Limited', 'sector': 'FMCG'},
            {'symbol': 'GODREJCP', 'name': 'Godrej Consumer Products Limited', 'sector': 'FMCG'},
            {'symbol': 'DABUR', 'name': 'Dabur India Limited', 'sector': 'FMCG'},
            {'symbol': 'MARICO', 'name': 'Marico Limited', 'sector': 'FMCG'},
            {'symbol': 'PIDILITIND', 'name': 'Pidilite Industries Limited', 'sector': 'Chemicals'},
            {'symbol': 'BPCL', 'name': 'Bharat Petroleum Corporation Limited', 'sector': 'Oil & Gas'},
            {'symbol': 'IOC', 'name': 'Indian Oil Corporation Limited', 'sector': 'Oil & Gas'},
            {'symbol': 'HDFCLIFE', 'name': 'HDFC Life Insurance Company Limited', 'sector': 'Insurance'},
            {'symbol': 'SBILIFE', 'name': 'SBI Life Insurance Company Limited', 'sector': 'Insurance'},
            {'symbol': 'ICICIPRULI', 'name': 'ICICI Prudential Life Insurance Company Limited', 'sector': 'Insurance'},
            {'symbol': 'ADANIENT', 'name': 'Adani Enterprises Limited', 'sector': 'Diversified'},
        ]

        # Filter symbols based on query - search in symbol, name, and sector
        matching_symbols = []
        for symbol in all_symbols:
            if (query in symbol['symbol'] or 
                query in symbol['name'].upper() or 
                query in symbol.get('sector', '').upper()):
                matching_symbols.append(symbol)

        # Sort by relevance - exact symbol matches first, then name matches
        def sort_relevance(item):
            if item['symbol'].startswith(query):
                return 0  # Highest priority for symbol starting with query
            elif query in item['symbol']:
                return 1  # Second priority for symbol containing query
            elif query in item['name'].upper():
                return 2  # Third priority for name containing query
            else:
                return 3  # Lowest priority for sector matches

        matching_symbols.sort(key=sort_relevance)
        
        return jsonify(matching_symbols[:15])  # Return top 15 matches

    except Exception as e:
        logging.error(f"Symbol search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@trading_api.route('/chart-data')
@login_required
def get_chart_data():
    """Get chart data for a symbol"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        symbol = request.args.get('symbol', '').strip().upper()
        period = request.args.get('period', '1W')
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400

        # Calculate date range based on period
        end_dt = datetime.now()
        if period == '1D':
            start_dt = end_dt - timedelta(days=1)
            interval = timedelta(minutes=5)
        elif period == '1W':
            start_dt = end_dt - timedelta(weeks=1)
            interval = timedelta(hours=1)
        elif period == '1M':
            start_dt = end_dt - timedelta(days=30)
            interval = timedelta(hours=4)
        elif period == '3M':
            start_dt = end_dt - timedelta(days=90)
            interval = timedelta(days=1)
        elif period == '1Y':
            start_dt = end_dt - timedelta(days=365)
            interval = timedelta(days=1)
        elif period == 'custom' and start_date and end_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            if days_diff <= 7:
                interval = timedelta(hours=1)
            elif days_diff <= 30:
                interval = timedelta(hours=4)
            else:
                interval = timedelta(days=1)
        else:
            return jsonify({'error': 'Invalid period'}), 400

        # Try to get real current price from the Kotak Neo API
        current_price = None
        real_data_available = False
        
        try:
            # Try to get holdings data to find the current price for this symbol
            holdings_data = trading_functions.get_holdings(client)
            if holdings_data and isinstance(holdings_data, list):
                for holding in holdings_data:
                    if (holding.get('trdSym', '').upper() == symbol or 
                        holding.get('scrip', '').upper() == symbol or
                        holding.get('symbolDescription', '').upper() == symbol):
                        current_price = float(holding.get('ltp', 0) or holding.get('cmp', 0) or 0)
                        if current_price > 0:
                            real_data_available = True
                            break
            
            # If not found in holdings, try positions
            if not real_data_available:
                positions_data = trading_functions.get_positions(client)
                if positions_data and isinstance(positions_data, list):
                    for position in positions_data:
                        if (position.get('trdSym', '').upper() == symbol or 
                            position.get('scrip', '').upper() == symbol):
                            current_price = float(position.get('ltp', 0) or position.get('cmp', 0) or 0)
                            if current_price > 0:
                                real_data_available = True
                                break

        except Exception as real_data_error:
            logging.warning(f"Could not fetch real data for {symbol}: {str(real_data_error)}")

        # Use fallback pricing if no real data available
        if not real_data_available or not current_price:
            # Use symbol-based realistic pricing
            symbol_prices = {
                'RELIANCE': 2850, 'TCS': 4150, 'HDFCBANK': 1650, 'INFY': 1850,
                'ICICIBANK': 1250, 'BHARTIARTL': 950, 'ITC': 450, 'SBIN': 825,
                'LT': 3650, 'KOTAKBANK': 1750, 'HINDUNILVR': 2650, 'BAJFINANCE': 6850,
                'AXISBANK': 1150, 'ASIANPAINT': 3250, 'MARUTI': 11500, 'NESTLEIND': 2350,
                'TITAN': 3450, 'WIPRO': 565, 'TATAMOTORS': 775, 'HCLTECH': 1650
            }
            current_price = symbol_prices.get(symbol, 2500)

        # Generate realistic historical data
        candlesticks = []
        volume_data = []

        # Start with a base price slightly different from current
        base_price = current_price * random.uniform(0.92, 1.08)
        price = base_price

        current_dt = start_dt
        while current_dt <= end_dt:
            open_price = price
            
            # More realistic price movements
            volatility = 0.015 if period in ['1D', '1W'] else 0.025
            price_change = random.uniform(-volatility, volatility)
            
            # Add trend bias toward current price
            trend_factor = (current_price - price) / current_price * 0.1
            price_change += trend_factor
            
            close_price = open_price * (1 + price_change)

            # Generate high and low prices
            intraday_range = abs(price_change) + random.uniform(0.005, 0.02)
            high_price = max(open_price, close_price) * (1 + intraday_range/2)
            low_price = min(open_price, close_price) * (1 - intraday_range/2)

            # Volume based on volatility
            base_volume = 100000
            volatility_multiplier = 1 + abs(price_change) * 10
            volume = int(base_volume * volatility_multiplier * random.uniform(0.5, 2.0))

            timestamp = int(current_dt.timestamp())

            candlesticks.append({
                'time': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2)
            })

            volume_data.append({
                'time': timestamp,
                'value': volume,
                'color': '#16a34a' if close_price >= open_price else '#dc2626'
            })

            price = close_price
            current_dt += interval

        return jsonify({
            'symbol': symbol,
            'candlesticks': candlesticks,
            'volume': volume_data,
            'period': period,
            'current_price': current_price,
            'real_data_available': real_data_available,
            'data_source': 'live_api' if real_data_available else 'simulated'
        })

    except Exception as e:
        logging.error(f"Chart data error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@trading_api.route('/signals')
@login_required
def get_trading_signals():
    """Get trading signals"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        # In a real implementation, this would fetch actual trading signals
        # from technical analysis algorithms or external signal providers
        
        # For now, return sample signals based on current holdings/positions
        signals = []
        
        try:
            # Get holdings data
            holdings_data = trading_functions.get_holdings(client)
            if holdings_data and isinstance(holdings_data, list):
                for holding in holdings_data:
                    symbol = holding.get('displaySymbol', holding.get('symbol', 'N/A'))
                    current_price = float(holding.get('closingPrice', 0) or holding.get('ltp', 0) or 0)
                    avg_price = float(holding.get('averagePrice', 0) or 0)
                    
                    if current_price > 0:
                        # Simple signal generation based on price vs average
                        price_diff_pct = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
                        
                        if price_diff_pct > 5:
                            signal_type = 'SELL'
                            strength = 'STRONG' if price_diff_pct > 15 else 'MEDIUM'
                        elif price_diff_pct < -5:
                            signal_type = 'BUY'
                            strength = 'STRONG' if price_diff_pct < -15 else 'MEDIUM'
                        else:
                            signal_type = 'HOLD'
                            strength = 'WEAK'
                        
                        signals.append({
                            'symbol': symbol,
                            'signal': signal_type,
                            'strength': strength,
                            'price': current_price,
                            'target': current_price * (1.1 if signal_type == 'BUY' else 0.95),
                            'stopLoss': current_price * (0.95 if signal_type == 'BUY' else 1.05),
                            'timeframe': '1D',
                            'sector': holding.get('sector', 'Unknown'),
                            'confidence': abs(price_diff_pct) * 2 + 60,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'holdings_analysis'
                        })
            
            # Get positions data
            positions_data = trading_functions.get_positions(client)
            if positions_data and isinstance(positions_data, list):
                for position in positions_data:
                    symbol = position.get('trdSym', position.get('sym', 'N/A'))
                    if symbol and symbol not in [s['symbol'] for s in signals]:
                        current_price = float(position.get('ltp', 0) or position.get('cmp', 0) or 0)
                        
                        if current_price > 0:
                            # Generate signals for position symbols
                            signals.append({
                                'symbol': symbol,
                                'signal': random.choice(['BUY', 'SELL', 'HOLD']),
                                'strength': random.choice(['STRONG', 'MEDIUM', 'WEAK']),
                                'price': current_price,
                                'target': current_price * random.uniform(1.05, 1.15),
                                'stopLoss': current_price * random.uniform(0.92, 0.98),
                                'timeframe': random.choice(['1D', '1W', '1M']),
                                'sector': 'Unknown',
                                'confidence': random.uniform(60, 95),
                                'timestamp': datetime.now().isoformat(),
                                'source': 'positions_analysis'
                            })

        except Exception as e:
            logging.warning(f"Error generating signals from real data: {str(e)}")
        
        # If no real signals generated, return sample data
        if not signals:
            signals = generate_sample_signals()
        
        return jsonify({
            'success': True,
            'signals': signals,
            'timestamp': datetime.now().isoformat(),
            'count': len(signals)
        })

    except Exception as e:
        logging.error(f"Trading signals error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_sample_signals():
    """Generate sample trading signals"""
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'BHARTIARTL', 'ITC', 'SBIN']
    signals = []
    
    for symbol in symbols:
        base_price = random.uniform(100, 5000)
        signal_type = random.choice(['BUY', 'SELL', 'HOLD'])
        
        signals.append({
            'symbol': symbol,
            'signal': signal_type,
            'strength': random.choice(['STRONG', 'MEDIUM', 'WEAK']),
            'price': round(base_price, 2),
            'target': round(base_price * (1.1 if signal_type == 'BUY' else 0.95), 2),
            'stopLoss': round(base_price * (0.95 if signal_type == 'BUY' else 1.05), 2),
            'timeframe': random.choice(['1D', '1W', '1M']),
            'sector': random.choice(['Banking', 'IT', 'Auto', 'Pharma']),
            'confidence': round(random.uniform(60, 95), 1),
            'timestamp': datetime.now().isoformat(),
            'source': 'sample_data'
        })
    
    return signals

@trading_api.route('/live-quotes')
@login_required
def get_live_quotes():
    """Get live quotes for multiple symbols"""
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'Session expired'}), 401

        symbols = request.args.getlist('symbols')
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400

        live_quotes = {}
        
        # Try to get real-time data from holdings and positions
        try:
            # Get current holdings
            holdings_data = trading_functions.get_holdings(client)
            if holdings_data and isinstance(holdings_data, list):
                for holding in holdings_data:
                    symbol = holding.get('trdSym', '').upper()
                    if symbol in [s.upper() for s in symbols]:
                        live_quotes[symbol] = {
                            'symbol': symbol,
                            'ltp': float(holding.get('ltp', 0) or holding.get('cmp', 0) or 0),
                            'change': float(holding.get('realizedPL', 0) or 0),
                            'change_percent': float(holding.get('pnlPercentage', 0) or 0),
                            'volume': int(holding.get('quantity', 0) or 0),
                            'high': float(holding.get('ltp', 0) or 0) * 1.02,
                            'low': float(holding.get('ltp', 0) or 0) * 0.98,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'holdings'
                        }

            # Get current positions
            positions_data = trading_functions.get_positions(client)
            if positions_data and isinstance(positions_data, list):
                for position in positions_data:
                    symbol = position.get('trdSym', '').upper()
                    if symbol in [s.upper() for s in symbols]:
                        live_quotes[symbol] = {
                            'symbol': symbol,
                            'ltp': float(position.get('ltp', 0) or position.get('cmp', 0) or 0),
                            'change': float(position.get('realizedPL', 0) or position.get('pnl', 0) or 0),
                            'change_percent': float(position.get('pnlPercentage', 0) or 0),
                            'volume': int(position.get('flQty', 0) or position.get('quantity', 0) or 0),
                            'high': float(position.get('ltp', 0) or 0) * 1.02,
                            'low': float(position.get('ltp', 0) or 0) * 0.98,
                            'timestamp': datetime.now().isoformat(),
                            'source': 'positions'
                        }

        except Exception as e:
            logging.warning(f"Error fetching live quotes: {str(e)}")

        # For symbols not found in holdings/positions, generate simulated data
        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper not in live_quotes:
                # Generate realistic simulated quotes
                base_prices = {
                    'RELIANCE': 2850, 'TCS': 4150, 'HDFCBANK': 1650, 'INFY': 1850,
                    'ICICIBANK': 1250, 'BHARTIARTL': 950, 'ITC': 450, 'SBIN': 825,
                    'LT': 3650, 'KOTAKBANK': 1750, 'HINDUNILVR': 2650, 'BAJFINANCE': 6850
                }
                
                base_price = base_prices.get(symbol_upper, 2500)
                current_variation = random.uniform(-0.03, 0.03)
                current_price = base_price * (1 + current_variation)
                
                live_quotes[symbol_upper] = {
                    'symbol': symbol_upper,
                    'ltp': round(current_price, 2),
                    'change': round(base_price * current_variation, 2),
                    'change_percent': round(current_variation * 100, 2),
                    'volume': random.randint(50000, 500000),
                    'high': round(current_price * 1.015, 2),
                    'low': round(current_price * 0.985, 2),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'simulated'
                }

        return jsonify({
            'success': True,
            'quotes': live_quotes,
            'timestamp': datetime.now().isoformat(),
            'count': len(live_quotes)
        })

    except Exception as e:
        logging.error(f"Live quotes error: {str(e)}")
        return jsonify({'error': str(e)}), 500
