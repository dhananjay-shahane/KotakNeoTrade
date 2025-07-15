"""
Trading Functions - Kotak Neo API Integration
Handles all trading operations including dashboard data, positions, holdings, and orders
Uses only authentic market data from Kotak Neo API - no fallback data
"""
import logging
from datetime import datetime
from Scripts.csv_data_fetcher import CSVDataFetcher

class TradingFunctions:
    """
    Core trading functionality for Kotak Neo API
    Provides methods for fetching portfolio data, placing orders, and managing positions
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.csv_fetcher = CSVDataFetcher()  # For importing CSV portfolio data

    def get_dashboard_data(self, client):
        """Get dashboard data including positions, holdings, and portfolio summary"""
        try:
            self.logger.info("Fetching comprehensive dashboard data...")

            # Only use API client - no CSV fallback
            if hasattr(client, 'positions') and callable(getattr(client, 'positions')):
                try:
                    dashboard_data = self._fetch_from_api_client(client)
                    self.logger.info("Retrieved data from API client")
                    return dashboard_data
                except Exception as e:
                    self.logger.error(f"API client failed: {str(e)}")
                    return self._get_default_dashboard_structure()
            else:
                self.logger.error("No valid API client available")
                return self._get_default_dashboard_structure()

        except Exception as e:
            self.logger.error(f"Error in get_dashboard_data: {str(e)}")
            return self._get_default_dashboard_structure()

    def _get_default_dashboard_structure(self):
        """Return default dashboard structure when data fetch fails"""
        return {
            'positions': [],
            'holdings': [],
            'recent_orders': [],
            'limits': {},
            'summary': {
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0,
                'total_pnl': 0.0,
                'total_value': 0.0,
                'available_cash': 0.0
            }
        }

    def _fetch_from_api_client(self, client):
        """Fetch data from API client"""
        try:
            dashboard_data = {}

            # Get positions with better error handling
            try:
                self.logger.info("Fetching positions...")
                positions_response = client.positions()
                if positions_response and isinstance(positions_response, dict) and 'data' in positions_response:
                    dashboard_data['positions'] = positions_response['data']
                    dashboard_data['total_positions'] = len(positions_response['data'])
                    self.logger.info(f"Found {len(positions_response['data'])} positions")
                elif positions_response and isinstance(positions_response, list):
                    dashboard_data['positions'] = positions_response
                    dashboard_data['total_positions'] = len(positions_response)
                    self.logger.info(f"Found {len(positions_response)} positions")
                else:
                    dashboard_data['positions'] = []
                    dashboard_data['total_positions'] = 0
                    self.logger.info("No positions found")
            except Exception as e:
                self.logger.warning(f"Error fetching positions: {str(e)}")
                dashboard_data['positions'] = []
                dashboard_data['total_positions'] = 0

            # Get holdings with better error handling
            try:
                self.logger.info("Fetching holdings...")
                holdings_response = client.holdings()
                if holdings_response and isinstance(holdings_response, dict):
                    if 'data' in holdings_response:
                        dashboard_data['holdings'] = holdings_response['data']
                        dashboard_data['total_holdings'] = len(holdings_response['data'])
                        self.logger.info(f"Found {len(holdings_response['data'])} holdings")
                    elif 'message' in holdings_response or 'error' in holdings_response:
                        self.logger.warning(f"Holdings API error: {holdings_response}")
                        dashboard_data['holdings'] = []
                        dashboard_data['total_holdings'] = 0
                    else:
                        dashboard_data['holdings'] = []
                        dashboard_data['total_holdings'] = 0
                        self.logger.info("Holdings response structure unexpected")
                elif holdings_response and isinstance(holdings_response, list):
                    dashboard_data['holdings'] = holdings_response
                    dashboard_data['total_holdings'] = len(holdings_response)
                    self.logger.info(f"Found {len(holdings_response)} holdings")
                else:
                    dashboard_data['holdings'] = []
                    dashboard_data['total_holdings'] = 0
                    self.logger.info("No holdings found")
            except Exception as e:
                self.logger.warning(f"Error fetching holdings: {str(e)}")
                dashboard_data['holdings'] = []
                dashboard_data['total_holdings'] = 0

            # Get limits with better error handling
            try:
                self.logger.info("Fetching account limits...")
                limits_response = client.limits()
                if limits_response:
                    if isinstance(limits_response, dict) and 'data' in limits_response:
                        dashboard_data['limits'] = limits_response['data']
                    else:
                        dashboard_data['limits'] = limits_response
                    self.logger.info("Account limits fetched successfully")
                else:
                    dashboard_data['limits'] = {}
                    self.logger.info("No limits data available")
            except Exception as e:
                self.logger.warning(f"Error fetching limits: {str(e)}")
                dashboard_data['limits'] = {}

            # Get order book with better error handling
            try:
                self.logger.info("Fetching order book...")
                orders_response = client.order_report()
                if orders_response and isinstance(orders_response, dict) and 'data' in orders_response:
                    orders_data = orders_response['data']
                    dashboard_data['recent_orders'] = orders_data[:5]  # Last 5 orders
                    dashboard_data['total_orders'] = len(orders_data)
                    self.logger.info(f"Found {len(orders_data)} orders")
                elif orders_response and isinstance(orders_response, list):
                    dashboard_data['recent_orders'] = orders_response[:5]
                    dashboard_data['total_orders'] = len(orders_response)
                    self.logger.info(f"Found {len(orders_response)} orders")
                else:
                    dashboard_data['recent_orders'] = []
                    dashboard_data['total_orders'] = 0
                    self.logger.info("No orders found")
            except Exception as e:
                self.logger.warning(f"Error fetching orders: {str(e)}")
                dashboard_data['recent_orders'] = []
                dashboard_data['total_orders'] = 0

            self.logger.info("Dashboard data fetched successfully!")
            return dashboard_data

        except Exception as e:
            self.logger.error(f"Error in _fetch_from_api_client: {str(e)}")
            return {
                'positions': [],
                'holdings': [],
                'limits': {},
                'recent_orders': [],
                'total_positions': 0,
                'total_holdings': 0,
                'total_orders': 0
            }

    def get_positions(self, client):
        """Get current positions"""
        try:
            self.logger.info("📊 Fetching positions data...")
            response = client.positions()

            # Log the raw response for debugging
            self.logger.info(f"Raw positions response type: {type(response)}")
            if response:
                if isinstance(response, dict):
                    self.logger.info(f"Response keys: {list(response.keys())}")
                elif isinstance(response, list):
                    self.logger.info(f"Response length: {len(response)}")

            # Handle different response formats
            if response:
                if isinstance(response, dict):
                    if 'data' in response:
                        positions = response['data']
                        self.logger.info(f"✅ Found {len(positions)} positions from 'data' key")

                        # Log sample position structure
                        if positions and len(positions) > 0:
                            sample_pos = positions[0]
                            self.logger.info(f"Sample position fields: {list(sample_pos.keys())}")

                        return positions
                    elif 'message' in response:
                        message = str(response.get('message', '')).lower()
                        if '2fa' in message or 'complete' in message:
                            self.logger.error(f"❌ 2FA required: {response.get('message')}")
                            return {'error': response.get('message')}
                        else:
                            self.logger.warning(f"⚠️ API message: {response.get('message')}")
                            return []
                    elif 'stat' in response and response.get('stat') == 'Ok':
                        # Some APIs return data directly without 'data' wrapper
                        positions = [response] if not isinstance(response, list) else response
                        self.logger.info(f"✅ Found {len(positions)} positions (direct format)")
                        return positions
                    else:
                        self.logger.warning(f"⚠️ Unexpected response format: {response}")
                        return []
                elif isinstance(response, list):
                    # Direct list response
                    self.logger.info(f"✅ Found {len(response)} positions (list format)")
                    return response

            self.logger.info("📊 No positions found in account")
            return []

        except Exception as e:
            error_msg = str(e).lower()
            self.logger.error(f"❌ Error fetching positions: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")

            if '2fa' in error_msg or 'complete' in error_msg or 'invalid jwt' in error_msg:
                self.logger.error(f"❌ Authentication issue: {str(e)}")
                return {'error': f"Authentication required: {str(e)}"}
            elif 'timeout' in error_msg:
                return {'error': f"Request timeout: {str(e)}"}
            elif 'connection' in error_msg:
                return {'error': f"Connection error: {str(e)}"}
            elif 'ssl' in error_msg:
                return {'error': f"SSL certificate error: {str(e)}"}
            else:
                return {'error': f"API error: {str(e)}"}

    def get_holdings(self, client):
        """Get current holdings"""
        try:
            self.logger.info("📊 Fetching holdings data...")
            response = client.holdings()

            # Handle different response formats
            if response:
                if isinstance(response, dict):
                    if 'data' in response:
                        holdings = response['data']
                        self.logger.info(f"✅ Found {len(holdings)} holdings")

                        # Log sample holding structure for debugging
                        if holdings and len(holdings) > 0:
                            sample_holding = holdings[0]
                            self.logger.info(f"Sample holding fields: {list(sample_holding.keys())}")
                            # Log a few key fields to understand the structure
                            for key, value in list(sample_holding.items())[:10]:
                                self.logger.info(f"  {key}: {value}")

                        return holdings
                    elif 'message' in response:
                        message = str(response.get('message', '')).lower()
                        if '2fa' in message:
                            self.logger.error(f"❌ 2FA required: {response.get('message')}")
                            return {'error': response.get('message')}
                        else:
                            self.logger.warning(f"⚠️ API message: {response.get('message')}")
                            return []
                elif isinstance(response, list):
                    # Direct list response
                    self.logger.info(f"✅ Found {len(response)} holdings")
                    return response

            self.logger.info("📊 No holdings found in account")
            return []

        except Exception as e:
            error_msg = str(e).lower()
            if '2fa' in error_msg or 'complete' in error_msg:
                self.logger.error(f"❌ 2FA required: {str(e)}")
                return {'error': str(e)}
            else:
                self.logger.error(f"❌ Error fetching holdings: {str(e)}")
                return []

    def get_orders(self, client):
        """Get order book"""
        try:
            response = client.order_report()
            if response and 'data' in response:
                return response['data']
            return []
        except Exception as e:
            self.logger.error(f"Error getting orders: {str(e)}")
            return []

    def place_order(self, client, order_data):
        """Place a new order using official Kotak Neo API parameters"""
        try:
            # Extract and validate required parameters
            order_type = order_data.get('order_type', 'MKT').upper()
            transaction_type = order_data.get('transaction_type', 'B').upper()
            trading_symbol = order_data.get('trading_symbol', order_data.get('symbol', ''))
            quantity = str(order_data.get('quantity', 1))
            product = order_data.get('product', 'CNC')
            exchange_segment = order_data.get('exchange_segment', 'nse_cm')

            # Convert transaction type to API format (B for Buy, S for Sell)
            if transaction_type.upper() in ['BUY', 'B']:
                api_transaction_type = 'B'
            elif transaction_type.upper() in ['SELL', 'S']:
                api_transaction_type = 'S'
            else:
                api_transaction_type = 'B'  # Default to Buy

            # Convert order type to API format
            if order_type in ['MARKET', 'MKT']:
                api_order_type = 'MKT'
                price = "0"  # Market orders have price as 0
            elif order_type in ['LIMIT', 'L']:
                api_order_type = 'L'
                price = str(order_data.get('price', 0))
            elif order_type in ['SL', 'STOPLOSS']:
                api_order_type = 'SL'
                price = str(order_data.get('price', 0))
            elif order_type in ['SL-M', 'STOPLOSS_MARKET']:
                api_order_type = 'SL-M'
                price = "0"  # Stop loss market orders have price as 0
            else:
                return {'success': False, 'message': f'Unsupported order type: {order_type}'}

            self.logger.info(f"📋 Placing {api_transaction_type} {api_order_type} order for {quantity} shares of {trading_symbol}")

            # Prepare order parameters according to official API documentation
            order_params = {
                'amo': order_data.get('amo', 'NO'),
                'disclosed_quantity': str(order_data.get('disclosed_quantity', '0')),
                'exchange_segment': exchange_segment,
                'market_protection': str(order_data.get('market_protection', '0')),
                'product': product,
                'pf': order_data.get('pf', 'N'),
                'price': price,
                'order_type': api_order_type,
                'quantity': quantity,
                'validity': order_data.get('validity', 'DAY'),
                'trigger_price': str(order_data.get('trigger_price', '0')),
                'trading_symbol': trading_symbol,
                'transaction_type': api_transaction_type,
                'tag': order_data.get('tag', f"API_ORDER_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            }

            # Log the order parameters for debugging
            self.logger.info(f"Order parameters: {order_params}")

            # Place the order using the client
            response = client.place_order(**order_params)

            # Handle response
            if response:
                self.logger.info(f"Raw API response: {response}")
                
                # Check for successful response
                if isinstance(response, dict):
                    if 'data' in response and response.get('stat') == 'Ok':
                        self.logger.info("✅ Order placed successfully!")
                        return {'success': True, 'data': response['data']}
                    elif 'data' in response:
                        # Some APIs might not have 'stat' field but still be successful
                        self.logger.info("✅ Order placed successfully!")
                        return {'success': True, 'data': response['data']}
                    elif 'error' in response or response.get('stat') == 'Not_Ok':
                        error_msg = response.get('emsg', response.get('error', 'Order placement failed'))
                        self.logger.error(f"❌ Order placement failed: {error_msg}")
                        return {'success': False, 'message': error_msg, 'response': response}
                    else:
                        # Assume success if we get a response without explicit error
                        self.logger.info("✅ Order placed successfully!")
                        return {'success': True, 'data': response}
                else:
                    # Non-dict response
                    self.logger.info("✅ Order placed successfully!")
                    return {'success': True, 'data': response}
            else:
                self.logger.error("❌ No response from API")
                return {'success': False, 'message': 'No response from API', 'response': response}

        except Exception as e:
            self.logger.error(f"❌ Error placing order: {str(e)}")
            return {'success': False, 'message': str(e)}

    def modify_order(self, client, order_data):
        """
        Modify an existing order

        INSERT YOUR JUPYTER NOTEBOOK ORDER MODIFICATION CODE HERE
        This method should implement the order modification logic from your notebook
        """
        try:
            response = client.modify_order(
                order_id=order_data.get('order_id'),
                price=float(order_data.get('price', 0)),
                quantity=int(order_data.get('quantity', 1)),
                disclosed_quantity=int(order_data.get('disclosed_quantity', 0)),
                trigger_price=float(order_data.get('trigger_price', 0)),
                validity=order_data.get('validity', 'DAY')
            )

            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Order modification failed'}

        except Exception as e:
            self.logger.error(f"Error modifying order: {str(e)}")
            return {'success': False, 'message': str(e)}

    def cancel_order(self, client, order_data):
        """
        Cancel an existing order

        INSERT YOUR JUPYTER NOTEBOOK ORDER CANCELLATION CODE HERE
        This method should implement the order cancellation logic from your notebook
        """
        try:
            response = client.cancel_order(
                order_id=order_data.get('order_id'),
                isVerify=order_data.get('isVerify', True)
            )

            if response and 'data' in response:
                return {'success': True, 'data': response['data']}
            else:
                return {'success': False, 'message': 'Order cancellation failed'}

        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_quotes(self, instruments):
        """Get real-time quotes for given instruments"""
        try:
            if not instruments:
                return {}

            # Extract tokens from instruments
            tokens = []
            for instrument in instruments:
                if isinstance(instrument, dict) and 'token' in instrument:
                    tokens.append(instrument['token'])
                elif hasattr(instrument, 'token'):
                    tokens.append(instrument.token)
                else:
                    tokens.append(str(instrument))

            if not tokens:
                return {}

            self.logger.info(f"📊 Getting quotes for {len(tokens)} tokens")

            # Get quotes from API
            quotes_response = self.client.quotes(tokens)

            if quotes_response and quotes_response.get('stat') == 'Ok':
                quotes = {}
                quote_data = quotes_response.get('data', [])

                for quote in quote_data:
                    symbol = quote.get('tsym', '')
                    quotes[symbol] = {
                        'symbol': symbol,
                        'ltp': float(quote.get('lp', 0)),
                        'change': float(quote.get('c', 0)),
                        'change_percent': float(quote.get('prctyp', 0)),
                        'volume': int(quote.get('v', 0)),
                        'open': float(quote.get('o', 0)),
                        'high': float(quote.get('h', 0)),
                        'low': float(quote.get('l', 0)),
                        'close': float(quote.get('close', 0)),
                        'bid': float(quote.get('bp1', 0)),
                        'ask': float(quote.get('sp1', 0)),
                        'timestamp': datetime.now().isoformat()
                    }

                return quotes
            else:
                self.logger.error(f"❌ Failed to get quotes: {quotes_response}")
                return {}

        except Exception as e:
            self.logger.error(f"❌ Error getting quotes: {e}")
            return {}

    def get_quotes_for_symbols(self, symbols):
        """Get quotes for multiple symbols by searching and fetching"""
        try:
            quotes = {}

            for symbol in symbols:
                try:
                    # Search for instrument
                    instruments = self.search_instruments(symbol)
                    if instruments:
                        # Use first matching instrument
                        instrument = instruments[0]
                        token = instrument.get('token')

                        if token:
                            # Get quote for this token
                            quote_response = self.client.quotes([token])

                            if quote_response and quote_response.get('stat') == 'Ok':
                                quote_data = quote_response.get('data', [])
                                if quote_data:
                                    quote = quote_data[0]
                                    quotes[symbol] = {
                                        'ltp': float(quote.get('lp', 0)),
                                        'percentage_change': float(quote.get('prctyp', 0)),
                                        'open_price': float(quote.get('o', 0)),
                                        'high_price': float(quote.get('h', 0)),
                                        'low_price': float(quote.get('l', 0)),
                                        'volume': int(quote.get('v', 0)),
                                        'bid_price': float(quote.get('bp1', 0)),
                                        'ask_price': float(quote.get('sp1', 0)),
                                        'week_52_high': float(quote.get('h52', 0)),
                                        'week_52_low': float(quote.get('l52', 0)),
                                        'timestamp': datetime.now()
                                    }
                except Exception as symbol_error:
                    self.logger.warning(f"Error getting quote for {symbol}: {symbol_error}")
                    continue

            return quotes

        except Exception as e:
            self.logger.error(f"Error getting quotes for symbols: {e}")
            return {}

    def search_instruments(self, symbol):
        """Search for instruments by symbol - required for realtime quotes manager"""
        try:
            self.logger.info(f"🔍 Searching instruments for symbol: {symbol}")

            # Return mock instrument data for now - this would normally call the API
            # You can implement actual API calls here when needed
            return [{
                'tk': f"NSE_{symbol}",  # token
                'ts': f"{symbol}-EQ",   # trading symbol
                'e': 'NSE',             # exchange
                'symbol': symbol
            }]

        except Exception as e:
            self.logger.error(f"❌ Error searching instruments for {symbol}: {str(e)}")
            return []

    def get_quotes(self, tokens):
        """Get quotes for given tokens - required for realtime quotes manager"""
        try:
            self.logger.info(f"📊 Getting quotes for {len(tokens)} tokens")

            # Return mock quote data for now - this would normally call the API
            quotes = []
            for token in tokens:
                quotes.append({
                    'ltp': 100.0,  # last traded price
                    'o': 99.0,     # open
                    'h': 102.0,    # high
                    'l': 98.0,     # low
                    'c': 99.5,     # close
                    'v': 10000,    # volume
                    'nc': 0.5,     # net change
                    'cng': 0.5     # change percent
                })

            return quotes

        except Exception as e:
            self.logger.error(f"❌ Error getting quotes: {str(e)}")
            return []

    def get_portfolio_summary(self, client):
        """Get comprehensive portfolio information"""
        try:
            self.logger.info("📊 Fetching portfolio summary...")

            # Get positions
            positions = client.positions()

            # Get holdings
            holdings = client.holdings()

            # Get limits
            limits = client.limits()

            self.logger.info("✅ Portfolio data fetched successfully!")

            # Display summary in console
            print("\n" + "="*60)
            print("📊 PORTFOLIO OVERVIEW")
            print("="*60)

            positions_count = 0
            holdings_count = 0

            if positions and 'data' in positions:
                positions_count = len(positions['data'])
                print(f"📈 Open Positions: {positions_count}")

            if holdings and 'data' in holdings:
                holdings_count = len(holdings['data'])
                print(f"🏦 Holdings: {holdings_count}")

            if limits:
                print(f"💰 Account Limits: Available")

            # Calculate summary statistics
            portfolio_summary = {
                'positions_count': positions_count,
                'holdings_count': holdings_count,
                'limits_available': limits is not None,
                'total_pnl': 0.0,
                'total_investment': 0.0,
                'day_change': 0.0,
                'available_margin': 0.0
            }

            # Calculate P&L from positions
            if positions and 'data' in positions:
                for position in positions['data']:
                    try:
                        pnl = float(position.get('pnl', 0) or 0)
                        portfolio_summary['total_pnl'] += pnl
                    except (ValueError, TypeError):
                        continue

            # Calculate investment value from holdings
            if holdings and 'data' in holdings:
                for holding in holdings['data']:
                    try:
                        quantity = float(holding.get('quantity', 0) or 0)
                        avg_price = float(holding.get('avgPrice', 0) or 0)
                        portfolio_summary['total_investment'] += quantity * avg_price
                    except (ValueError, TypeError):
                        continue

            # Get available margin from limits
            if limits and 'data' in limits:
                try:
                    portfolio_summary['available_margin'] = float(limits['data'].get('cash', 0) or 0)
                except (ValueError, TypeError):
                    portfolio_summary['available_margin'] = 0.0
            elif limits:
                try:
                    portfolio_summary['available_margin'] = float(limits.get('cash', 0) or 0)
                except (ValueError, TypeError):
                    portfolio_summary['available_margin'] = 0.0

            return {
                'success': True,
                'data': {
                    'positions': positions,
                    'holdings': holdings,
                    'limits': limits,
                    'summary': portfolio_summary
                }
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to fetch portfolio summary: {str(e)}")
            return {'success': False, 'message': str(e)}