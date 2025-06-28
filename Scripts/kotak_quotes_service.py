"""
Kotak Neo Quotes Service - Enhanced data collection for comprehensive market data
Integrates with Kotak Neo API to populate kotak_neo_quotes table
"""
import logging
from datetime import datetime, timedelta
from app import app, db
from Scripts.models_etf import KotakNeoQuote, AdminTradeSignal
from Scripts.trading_functions import TradingFunctions
import json

logger = logging.getLogger(__name__)

class KotakQuotesService:
    """Enhanced service for comprehensive Kotak Neo quotes data collection"""
    
    def __init__(self):
        self.trading_functions = TradingFunctions()
        self.etf_symbols = [
            'NIFTYBEES', 'BANKBEES', 'LIQUIDBEES', 'GOLDSHARE', 'ITBEES',
            'JUNIORBEES', 'HDFCNIFTY', 'ICICINIFTY', 'RELGOLD', 'HDFCGOLD',
            'AXISGOLD', 'KOTAKSILV', 'KOTAKNV20', 'KOTAKPSU', 'PSUBNKBEES',
            'ICICIB22', 'ICICIPRUH', 'ICICINXT50', 'CPSE ETF', 'AXISBNK'
        ]
    
    def fetch_comprehensive_quote_data(self, symbol):
        """Fetch comprehensive quote data for a symbol from Kotak Neo API"""
        try:
            # Search for instrument to get token
            instruments = self.trading_functions.search_instruments(symbol)
            if not instruments:
                logger.warning(f"No instruments found for symbol: {symbol}")
                return None
            
            instrument = instruments[0]
            token = instrument.get('token')
            trading_symbol = instrument.get('trading_symbol', symbol)
            exchange = instrument.get('exchange', 'NSE')
            
            # Get comprehensive quote data
            quotes = self.trading_functions.get_quotes([token])
            if not quotes or not quotes.get('data'):
                logger.warning(f"No quote data received for {symbol}")
                return None
            
            quote_data = quotes['data'][0] if isinstance(quotes['data'], list) else quotes['data']
            
            # Parse comprehensive quote data according to Kotak Neo API structure
            return {
                'symbol': symbol,
                'trading_symbol': trading_symbol,
                'token': str(token),
                'exchange': exchange,
                'segment': quote_data.get('segment', 'EQ'),
                'instrument_type': quote_data.get('instrument_type', 'EQ'),
                'ltp': float(quote_data.get('ltp', quote_data.get('last_price', 100.0))),
                'open_price': float(quote_data.get('open_price', quote_data.get('open', 0))),
                'high_price': float(quote_data.get('high_price', quote_data.get('high', 0))),
                'low_price': float(quote_data.get('low_price', quote_data.get('low', 0))),
                'close_price': float(quote_data.get('close_price', quote_data.get('prev_close', 0))),
                'net_change': float(quote_data.get('net_change', quote_data.get('change', 0))),
                'percentage_change': float(quote_data.get('percentage_change', quote_data.get('percent_change', 0))),
                'volume': int(quote_data.get('volume', 0)),
                'value': float(quote_data.get('value', quote_data.get('turnover', 0))),
                'bid_price': float(quote_data.get('bid_price', quote_data.get('bid', 0))),
                'ask_price': float(quote_data.get('ask_price', quote_data.get('ask', 0))),
                'bid_size': int(quote_data.get('bid_size', quote_data.get('bid_qty', 0))),
                'ask_size': int(quote_data.get('ask_size', quote_data.get('ask_qty', 0))),
                'upper_circuit': float(quote_data.get('upper_circuit', quote_data.get('uc_limit', 0))),
                'lower_circuit': float(quote_data.get('lower_circuit', quote_data.get('lc_limit', 0))),
                'week_52_high': float(quote_data.get('week_52_high', quote_data.get('yearly_high', 0))),
                'week_52_low': float(quote_data.get('week_52_low', quote_data.get('yearly_low', 0))),
                'avg_price': float(quote_data.get('avg_price', quote_data.get('vwap', 0))),
                'last_trade_time': datetime.now(),
                'market_status': quote_data.get('market_status', 'OPEN'),
                'lot_size': int(quote_data.get('lot_size', 1)),
                'tick_size': float(quote_data.get('tick_size', 0.05))
            }
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive quote for {symbol}: {e}")
            return None
    
    def update_kotak_neo_quotes(self):
        """Update KotakNeoQuote table with latest market data"""
        try:
            updated_count = 0
            
            for symbol in self.etf_symbols:
                quote_data = self.fetch_comprehensive_quote_data(symbol)
                if not quote_data:
                    continue
                
                # Check if quote already exists for today
                existing_quote = KotakNeoQuote.query.filter_by(
                    symbol=symbol
                ).filter(
                    KotakNeoQuote.timestamp >= datetime.now().date()
                ).order_by(KotakNeoQuote.timestamp.desc()).first()
                
                if existing_quote:
                    # Update existing quote
                    for key, value in quote_data.items():
                        if hasattr(existing_quote, key):
                            setattr(existing_quote, key, value)
                    existing_quote.timestamp = datetime.now()
                else:
                    # Create new quote
                    new_quote = KotakNeoQuote(**quote_data)
                    db.session.add(new_quote)
                
                updated_count += 1
                logger.info(f"Updated comprehensive quote for {symbol}: ₹{quote_data['ltp']}")
            
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} comprehensive quotes")
            
            # Also update admin trade signals with latest prices
            self.update_admin_signals_with_quotes()
            
            return updated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating Kotak Neo quotes: {e}")
            return 0
    
    def update_admin_signals_with_quotes(self):
        """Update admin trade signals with latest quote data"""
        try:
            # Get all active admin signals
            active_signals = AdminTradeSignal.query.filter_by(status='ACTIVE').all()
            
            for signal in active_signals:
                # Get latest comprehensive quote
                latest_quote = KotakNeoQuote.query.filter_by(
                    symbol=signal.symbol
                ).order_by(KotakNeoQuote.timestamp.desc()).first()
                
                if latest_quote:
                    # Update signal with latest market data
                    signal.current_price = latest_quote.ltp
                    signal.change_percent = latest_quote.percentage_change
                    signal.last_update_time = datetime.now()
                    
                    # Calculate P&L if entry price exists
                    if signal.entry_price:
                        pnl_amount = (float(latest_quote.ltp) - float(signal.entry_price)) * signal.quantity
                        pnl_percentage = ((float(latest_quote.ltp) - float(signal.entry_price)) / float(signal.entry_price)) * 100
                        
                        signal.pnl = pnl_amount
                        signal.pnl_percentage = pnl_percentage
                        signal.current_value = float(latest_quote.ltp) * signal.quantity
                        signal.investment_amount = float(signal.entry_price) * signal.quantity
            
            db.session.commit()
            logger.info(f"Updated {len(active_signals)} admin signals with latest quotes")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating admin signals with quotes: {e}")
    
    def get_comprehensive_market_data(self, symbols=None):
        """Get comprehensive market data for ETF signals page"""
        try:
            if symbols is None:
                symbols = self.etf_symbols
            
            market_data = {}
            
            for symbol in symbols:
                # Get latest comprehensive quote
                latest_quote = KotakNeoQuote.query.filter_by(
                    symbol=symbol
                ).order_by(KotakNeoQuote.timestamp.desc()).first()
                
                if latest_quote:
                    market_data[symbol] = latest_quote.to_dict()
                else:
                    # Fallback to basic quote if comprehensive not available
                    basic_data = self.fetch_comprehensive_quote_data(symbol)
                    if basic_data:
                        market_data[symbol] = basic_data
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive market data: {e}")
            return {}
    
    def start_comprehensive_data_collection(self):
        """Start comprehensive data collection for all ETF symbols"""
        logger.info("Starting comprehensive Kotak Neo quotes data collection...")
        
        # Initial data population
        updated_count = self.update_kotak_neo_quotes()
        
        if updated_count > 0:
            logger.info(f"✅ Successfully populated {updated_count} comprehensive quotes")
            return True
        else:
            logger.warning("❌ No quotes were updated")
            return False

def populate_kotak_neo_quotes():
    """Standalone function to populate comprehensive quotes data"""
    with app.app_context():
        service = KotakQuotesService()
        return service.start_comprehensive_data_collection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting Kotak Neo comprehensive quotes data collection...")
    success = populate_kotak_neo_quotes()
    if success:
        print("✅ Comprehensive quotes data populated successfully!")
    else:
        print("❌ Failed to populate comprehensive quotes data")