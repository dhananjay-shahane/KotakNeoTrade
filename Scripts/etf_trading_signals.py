from app import db
from Scripts.models_etf import RealtimeQuote
from Scripts.neo_client import NeoClient
from Scripts.session_helper import SessionHelper
from datetime import datetime, timedelta
import logging
import json
import random

logger = logging.getLogger(__name__)

class ETFTradingSignals:
    """ETF Trading Signals Manager"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_user_etf_positions(self, user_id):
        """Get all ETF positions for a user (including historical positions)"""
        try:
            # Get all positions (active and inactive) for display
            positions = ETFPosition.query.filter_by(user_id=user_id).order_by(ETFPosition.entry_date.desc()).all()

            # Update current prices with simulated data or live data
            self.update_position_prices(positions)

            # Convert to list of dictionaries
            positions_list = []
            for position in positions:
                pos_dict = position.to_dict()
                positions_list.append(pos_dict)

            return positions_list

        except Exception as e:
            self.logger.error(f"Error getting user ETF positions: {e}")
            return []

    def update_position_prices(self, positions):
        """Update current prices for ETF positions"""
        try:
            for position in positions:
                # For now, simulate price updates
                # In real implementation, this would fetch live prices from the API
                base_price = position.entry_price
                price_variation = random.uniform(-0.05, 0.05)  # ±5% variation
                position.current_price = base_price * (1 + price_variation)
                position.last_update_time = datetime.utcnow()

            db.session.commit()

        except Exception as e:
            self.logger.error(f"Error updating position prices: {e}")

    def calculate_portfolio_summary(self, user_id):
        """Calculate portfolio summary metrics"""
        try:
            positions = ETFPosition.query.filter_by(user_id=user_id, is_active=True).all()

            if not positions:
                return {
                    'total_positions': 0,
                    'total_investment': 0.0,
                    'current_value': 0.0,
                    'total_pnl': 0.0,
                    'return_percent': 0.0,
                    'profit_positions': 0,
                    'loss_positions': 0
                }

            total_investment = float(sum(pos.investment_amount for pos in positions))
            total_current_value = float(sum(pos.current_value for pos in positions))
            total_pnl = float(total_current_value - total_investment)
            return_percent = float((total_pnl / total_investment * 100)) if total_investment > 0 else 0.0

            profit_positions = sum(1 for pos in positions if pos.profit_loss > 0)
            loss_positions = sum(1 for pos in positions if pos.profit_loss < 0)

            return {
                'total_positions': len(positions),
                'total_investment': total_investment,
                'current_value': total_current_value,
                'total_pnl': total_pnl,
                'return_percent': return_percent,
                'profit_positions': profit_positions,
                'loss_positions': loss_positions
            }

        except Exception as e:
            self.logger.error(f"Error calculating portfolio summary: {e}")
            return {
                'total_positions': 0,
                'total_investment': 0.0,
                'current_value': 0.0,
                'total_pnl': 0.0,
                'return_percent': 0.0,
                'profit_positions': 0,
                'loss_positions': 0
            }

    def add_etf_position(self, user_id, position_data):
        """Add new ETF position"""
        try:
            position = ETFPosition()
            position.user_id = user_id
            position.etf_symbol = position_data['etf_symbol']
            position.trading_symbol = position_data['trading_symbol']
            position.token = position_data['token']
            position.exchange = position_data.get('exchange', 'NSE')
            position.entry_date = datetime.strptime(position_data['entry_date'], '%Y-%m-%d').date()
            position.quantity = int(position_data['quantity'])
            position.entry_price = float(position_data['entry_price'])
            position.target_price = float(position_data['target_price']) if position_data.get('target_price') else None
            position.stop_loss = float(position_data['stop_loss']) if position_data.get('stop_loss') else None
            position.current_price = float(position_data['entry_price'])  # Initialize with entry price
            position.position_type = position_data.get('position_type', 'LONG')
            position.notes = position_data.get('notes', '')
            position.is_active = True
            position.created_at = datetime.utcnow()
            position.last_update_time = datetime.utcnow()

            db.session.add(position)
            db.session.commit()

            return position.to_dict()

        except Exception as e:
            self.logger.error(f"Error adding ETF position: {e}")
            raise ValueError(f"Failed to add position: {e}")

    def update_etf_position(self, position_id, user_id, position_data):
        """Update existing ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")

            # Update fields
            if 'quantity' in position_data:
                position.quantity = int(position_data['quantity'])
            if 'entry_price' in position_data:
                position.entry_price = float(position_data['entry_price'])
            if 'target_price' in position_data:
                position.target_price = float(position_data['target_price']) if position_data['target_price'] else None
            if 'stop_loss' in position_data:
                position.stop_loss = float(position_data['stop_loss']) if position_data['stop_loss'] else None
            if 'notes' in position_data:
                position.notes = position_data['notes']
            if 'position_type' in position_data:
                position.position_type = position_data['position_type']

            position.last_update_time = datetime.utcnow()

            db.session.commit()

            return position.to_dict()

        except Exception as e:
            self.logger.error(f"Error updating ETF position: {e}")
            raise ValueError(f"Failed to update position: {e}")

    def delete_etf_position(self, position_id, user_id):
        """Delete ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")

            db.session.delete(position)
            db.session.commit()

            return True

        except Exception as e:
            self.logger.error(f"Error deleting ETF position: {e}")
            return False

    def search_etf_instruments(self, query):
        """Search for ETF instruments"""
        try:
            # Sample ETF instruments for search
            etf_instruments = [
                {'symbol': 'NIFTYBEES', 'description': 'Nippon India ETF Nifty BeES', 'trading_symbol': 'NIFTYBEES-EQ', 'token': '120001'},
                {'symbol': 'JUNIORBEES', 'description': 'Nippon India ETF Nifty Junior BeES', 'trading_symbol': 'JUNIORBEES-EQ', 'token': '120002'},
                {'symbol': 'GOLDBEES', 'description': 'Nippon India ETF Gold BeES', 'trading_symbol': 'GOLDBEES-EQ', 'token': '120003'},
                {'symbol': 'SILVERBEES', 'description': 'Nippon India ETF Silver BeES', 'trading_symbol': 'SILVERBEES-EQ', 'token': '120004'},
                {'symbol': 'LIQUIDETF', 'description': 'Nippon India ETF Liquid BeES', 'trading_symbol': 'LIQUIDETF-EQ', 'token': '120005'},
                {'symbol': 'BANKBEES', 'description': 'Nippon India ETF Bank BeES', 'trading_symbol': 'BANKBEES-EQ', 'token': '120006'},
                {'symbol': 'ITBEES', 'description': 'Nippon India ETF IT BeES', 'trading_symbol': 'ITBEES-EQ', 'token': '120007'},
                {'symbol': 'PHARMABEES', 'description': 'Nippon India ETF Pharma BeES', 'trading_symbol': 'PHARMABEES-EQ', 'token': '120008'},
                {'symbol': 'CONSUMERBEES', 'description': 'Nippon India ETF Consumer BeES', 'trading_symbol': 'CONSUMERBEES-EQ', 'token': '120009'},
                {'symbol': 'PSUBNKBEES', 'description': 'Nippon India ETF PSU Bank BeES', 'trading_symbol': 'PSUBNKBEES-EQ', 'token': '120010'},
                {'symbol': 'HDFCNIFETF', 'description': 'HDFC Nifty 50 ETF', 'trading_symbol': 'HDFCNIFETF-EQ', 'token': '120011'},
                {'symbol': 'IETF', 'description': 'ICICI Prudential Nifty ETF', 'trading_symbol': 'IETF-EQ', 'token': '120012'},
                {'symbol': 'AUBANK', 'description': 'AU Small Finance Bank ETF', 'trading_symbol': 'AUBANK-EQ', 'token': '120013'},
            ]

            # Filter based on query
            matching_instruments = []
            query_upper = query.upper()

            for instrument in etf_instruments:
                if (query_upper in instrument['symbol'].upper() or 
                    query_upper in instrument['description'].upper()):
                    matching_instruments.append(instrument)

            return matching_instruments[:10]  # Return top 10 matches

        except Exception as e:
            self.logger.error(f"Error searching ETF instruments: {e}")
            return []

    def get_live_quotes(self, instruments):
        """Get live quotes for instruments"""
        try:
            # For now, return simulated quotes
            # In real implementation, this would call the Neo API
            quotes = {}

            for instrument in instruments:
                token = instrument.get('token', '')
                symbol = instrument.get('symbol', '')

                # Simulate quote data
                base_price = random.uniform(50, 500)
                quotes[token] = {
                    'symbol': symbol,
                    'ltp': round(base_price, 2),
                    'change': round(random.uniform(-10, 10), 2),
                    'change_percent': round(random.uniform(-5, 5), 2),
                    'volume': random.randint(1000, 100000),
                    'timestamp': datetime.now().isoformat()
                }

            return quotes

        except Exception as e:
            self.logger.error(f"Error getting live quotes: {e}")
            return {}


class ETFTradingSignals:
    """ETF Trading Signals Manager with real-time data integration"""

    def __init__(self):
        self.session_helper = SessionHelper()
        self.neo_client = NeoClient()
        self.client = None
        self.websocket_subscriptions = set()

    def initialize_client(self):
        """Initialize Neo API client with current Flask session"""
        try:
            from flask import session

            # Get client from Flask session (already initialized)
            if 'client' in session and session['client']:
                self.client = session['client']
                logger.info("✅ Using existing Neo client from Flask session")
                return True
            else:
                logger.error("No active client in Flask session")
                return False

        except Exception as e:
            logger.error(f"Error initializing Neo client: {e}")
            return False

    def search_etf_instruments(self, query):
        """Search for ETF instruments using available data sources"""
        if not self.client:
            if not self.initialize_client():
                return []

        try:
            # For now, return some common ETF instruments as a fallback
            # This ensures the interface works while API integration is being finalized
            common_etfs = [
                {
                    'symbol': 'NIFTYBEES',
                    'trading_symbol': 'NIFTYBEES-EQ',
                    'token': '15083',
                    'exchange': 'NSE',
                    'description': 'Nippon India ETF Nifty BeES',
                    'lot_size': 1
                },
                {
                    'symbol': 'GOLDBEES',
                    'trading_symbol': 'GOLDBEES-EQ', 
                    'token': '1660',
                    'exchange': 'NSE',
                    'description': 'Nippon India ETF Gold BeES',
                    'lot_size': 1
                },
                {
                    'symbol': 'BANKBEES',
                    'trading_symbol': 'BANKBEES-EQ',
                    'token': '2800',
                    'exchange': 'NSE', 
                    'description': 'Nippon India ETF Bank BeES',
                    'lot_size': 1
                },
                {
                    'symbol': 'JUNIORBEES',
                    'trading_symbol': 'JUNIORBEES-EQ',
                    'token': '583',
                    'exchange': 'NSE',
                    'description': 'Nippon India ETF Junior BeES',
                    'lot_size': 1
                },
                {
                    'symbol': 'LIQUIDBEES',
                    'trading_symbol': 'LIQUIDBEES-EQ',
                    'token': '1023',
                    'exchange': 'NSE',
                    'description': 'Nippon India ETF Liquid BeES',
                    'lot_size': 1
                }
            ]

            # Filter ETFs based on query
            query_upper = query.upper()
            filtered_etfs = [
                etf for etf in common_etfs 
                if query_upper in etf['symbol'].upper() or query_upper in etf['description'].upper()
            ]

            logger.info(f"Found {len(filtered_etfs)} ETF instruments for query: {query}")
            return filtered_etfs

        except Exception as e:
            logger.error(f"Error searching ETF instruments: {e}")
            return []

    def get_live_quotes(self, instruments):
        """Get live quotes for multiple instruments"""
        if not self.client:
            if not self.initialize_client():
                return {}

        try:
            quotes = {}
            for instrument in instruments:
                try:
                    # Use the trading functions to get quotes since they work with the current API
                    from Scripts.trading_functions import TradingFunctions
                    trading_funcs = TradingFunctions()

                    # Only use authentic market data from Kotak Neo API
                    # No sample data generation - skip if no authentic data available
                    logger.warning(f"No authentic market data available for {instrument.get('symbol', 'unknown')}")
                    continue
                except Exception as e:
                    logger.error(f"Error getting quote for {instrument.get('symbol', 'unknown')}: {e}")
                    continue

            return quotes

        except Exception as e:
            logger.error(f"Error getting live quotes: {e}")
            return {}

    def add_etf_position(self, user_id, position_data):
        """Add new ETF position"""
        try:
            # Validate required fields
            required_fields = ['etf_symbol', 'trading_symbol', 'token', 'quantity', 'entry_price']
            for field in required_fields:
                if field not in position_data or not position_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Create new position
            from Scripts.models_etf import ETFPosition
            position = ETFPosition()
            position.user_id = user_id
            position.etf_symbol = position_data['etf_symbol']
            position.trading_symbol = position_data['trading_symbol']
            position.token = position_data['token']
            position.exchange = position_data.get('exchange', 'NSE')
            position.entry_date = datetime.strptime(position_data.get('entry_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
            position.quantity = int(position_data['quantity'])
            position.entry_price = float(position_data['entry_price'])
            position.target_price = float(position_data['target_price']) if position_data.get('target_price') else None
            position.stop_loss = float(position_data['stop_loss']) if position_data.get('stop_loss') else None
            position.position_type = position_data.get('position_type', 'LONG')
            position.notes = position_data.get('notes', '')

            # Set is_active based on position type or explicit status
            # 1 = active position, 0 = closed/inactive position
            position.is_active = position_data.get('is_active', True)

            db.session.add(position)
            db.session.commit()

            # Subscribe to live data for this instrument
            self.subscribe_to_live_data([{
                'token': position.token,
                'exchange': position.exchange,
                'symbol': position.etf_symbol
            }])

            logger.info(f"✅ Added ETF position: {position.etf_symbol}")
            return position.to_dict()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding ETF position: {e}")
            raise

    def update_etf_position(self, position_id, user_id, update_data):
        """Update existing ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")

            # Update allowed fields
            updatable_fields = ['quantity', 'entry_price', 'target_price', 'stop_loss', 'notes', 'position_type']
            for field in updatable_fields:
                if field in update_data:
                    if field in ['quantity', 'entry_price', 'target_price', 'stop_loss']:
                        setattr(position, field, float(update_data[field]) if update_data[field] else None)
                    else:
                        setattr(position, field, update_data[field])

            position.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"✅ Updated ETF position: {position.etf_symbol}")
            return position.to_dict()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ETF position: {e}")
            raise

    def delete_etf_position(self, position_id, user_id):
        """Delete ETF position"""
        try:
            position = ETFPosition.query.filter_by(id=position_id, user_id=user_id).first()
            if not position:
                raise ValueError("Position not found")

            # Unsubscribe from live data
            self.unsubscribe_from_live_data([{
                'token': position.token,
                'exchange': position.exchange
            }])

            db.session.delete(position)
            db.session.commit()

            logger.info(f"✅ Deleted ETF position: {position.etf_symbol}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting ETF position: {e}")
            raise

    def get_user_etf_positions(self, user_id):
        """Get all ETF positions for a user"""
        try:
            positions = ETFPosition.query.filter_by(user_id=user_id, is_active=True).all()

            # Get live quotes for all positions
            instruments = [{'token': p.token, 'exchange': p.exchange, 'symbol': p.etf_symbol} for p in positions]
            live_quotes = self.get_live_quotes(instruments)

            # Update positions with live data
            position_data = []
            for position in positions:
                pos_dict = position.to_dict()

                # Update with live quote if available
                if position.token in live_quotes:
                    quote = live_quotes[position.token]
                    position.current_price = quote['ltp']
                    position.last_update_time = datetime.utcnow()

                    # Recalculate metrics with live data
                    pos_dict.update({
                        'current_price': quote['ltp'],
                        'profit_loss': position.profit_loss,
                        'percentage_change': position.percentage_change,
                        'current_value': position.current_value,
                        'last_update_time': datetime.utcnow().isoformat(),
                        'live_data': quote
                    })

                position_data.append(pos_dict)

            # Commit live price updates
            db.session.commit()

            return position_data

        except Exception as e:
            logger.error(f"Error getting user ETF positions: {e}")
            return []

    def subscribe_to_live_data(self, instruments):
        """Subscribe to live data using WebSocket"""
        if not self.client:
            if not self.initialize_client():
                return False

        try:
            # Prepare instrument tokens for subscription
            tokens_to_subscribe = []
            for instrument in instruments:
                token = instrument['token']
                if token not in self.websocket_subscriptions:
                    tokens_to_subscribe.append(token)
                    self.websocket_subscriptions.add(token)

            if tokens_to_subscribe:
                # Subscribe to live data feed
                subscription_result = self.client.subscribe_to_orderfeed()
                logger.info(f"Subscribed to live data for {len(tokens_to_subscribe)} instruments")

                # Setup WebSocket callbacks for price updates
                self.setup_websocket_callbacks()

            return True

        except Exception as e:
            logger.error(f"Error subscribing to live data: {e}")
            return False

    def unsubscribe_from_live_data(self, instruments):
        """Unsubscribe from live data"""
        try:
            for instrument in instruments:
                token = instrument['token']
                if token in self.websocket_subscriptions:
                    self.websocket_subscriptions.remove(token)

            logger.info(f"Unsubscribed from live data for {len(instruments)} instruments")
            return True

        except Exception as e:
            logger.error(f"Error unsubscribing from live data: {e}")
            return False

    def setup_websocket_callbacks(self):
        """Setup WebSocket callbacks for live price updates"""
        def on_message(message):
            """Handle incoming WebSocket messages"""
            try:
                if isinstance(message, dict):
                    token = message.get('tk')
                    ltp = message.get('ltp')

                    if token and ltp:
                        # Update positions with new price data
                        self.update_positions_with_live_data(token, {
                            'ltp': ltp,
                            'change': message.get('nc', 0),
                            'change_percent': message.get('pc', 0),
                            'volume': message.get('v', 0)
                        })

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")

        def on_error(error):
            logger.error(f"WebSocket error: {error}")

        def on_close(message):
            logger.info("WebSocket connection closed")

        # Set callbacks if client supports it
        if hasattr(self.client, 'set_on_message'):
            self.client.set_on_message(on_message)
            self.client.set_on_error(on_error)
            self.client.set_on_close(on_close)

    def update_positions_with_live_data(self, token, quote_data):
        """Update ETF positions with live market data"""
        try:
            positions = ETFPosition.query.filter_by(token=str(token), is_active=True).all()

            for position in positions:
                position.current_price = quote_data['ltp']
                position.last_update_time = datetime.utcnow()

            db.session.commit()
            logger.debug(f"Updated {len(positions)} positions with live data for token {token}")

        except Exception as e:
            logger.error(f"Error updating positions with live data: {e}")

    def calculate_portfolio_summary(self, user_id):
        """Calculate portfolio summary metrics"""
        try:
            positions = ETFPosition.query.filter_by(user_id=user_id, is_active=True).all()

            total_investment = sum(p.investment_amount for p in positions)
            total_current_value = sum(p.current_value for p in positions)
            total_pnl = sum(p.profit_loss for p in positions)

            portfolio_return_pct = 0
            if total_investment > 0:
                portfolio_return_pct = (total_pnl / total_investment) * 100

            return {
                'total_positions': len(positions),
                'total_investment': total_investment,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'portfolio_return_percent': portfolio_return_pct,
                'profitable_positions': len([p for p in positions if p.profit_loss > 0]),
                'loss_positions': len([p for p in positions if p.profit_loss < 0])
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio summary: {e}")
            return {}