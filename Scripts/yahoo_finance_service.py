
import yfinance as yf
import logging
from datetime import datetime
from app import db
from Scripts.models_etf import AdminTradeSignal, RealtimeQuote
import time

logger = logging.getLogger(__name__)

class YahooFinanceService:
    def __init__(self):
        self.session = None
    
    def get_stock_price(self, symbol):
        """Fetch current price for a single symbol from Yahoo Finance"""
        try:
            # Add .NS suffix for NSE stocks if not already present
            yahoo_symbol = symbol
            if not yahoo_symbol.endswith('.NS') and not yahoo_symbol.endswith('.BO'):
                yahoo_symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if current_price:
                # Get additional data
                open_price = info.get('regularMarketOpen') or info.get('open')
                high_price = info.get('regularMarketDayHigh') or info.get('dayHigh')
                low_price = info.get('regularMarketDayLow') or info.get('dayLow')
                volume = info.get('regularMarketVolume') or info.get('volume')
                previous_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
                
                # Calculate change
                change_amount = 0
                change_percent = 0
                if previous_close and current_price:
                    change_amount = current_price - previous_close
                    change_percent = (change_amount / previous_close) * 100
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'volume': volume,
                    'change_amount': change_amount,
                    'change_percent': change_percent,
                    'previous_close': previous_close,
                    'timestamp': datetime.utcnow()
                }
            else:
                logger.warning(f"No price data found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    def get_multiple_prices(self, symbols):
        """Fetch prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            price_data = self.get_stock_price(symbol)
            if price_data:
                prices[symbol] = price_data
            time.sleep(0.1)  # Small delay to avoid rate limiting
        return prices
    
    def update_admin_signals_prices(self):
        """Update current prices in admin_trade_signals table"""
        try:
            # Get all active signals
            signals = AdminTradeSignal.query.filter_by(status='ACTIVE').all()
            
            if not signals:
                logger.info("No active signals to update")
                return 0
            
            symbols = list(set([signal.symbol for signal in signals]))
            logger.info(f"Updating prices for {len(symbols)} symbols")
            
            # Get prices from Yahoo Finance
            prices = self.get_multiple_prices(symbols)
            
            updated_count = 0
            for signal in signals:
                if signal.symbol in prices:
                    price_data = prices[signal.symbol]
                    
                    # Update current price
                    signal.current_price = price_data['current_price']
                    signal.last_update_time = datetime.utcnow()
                    
                    # Calculate change percentage
                    if signal.entry_price:
                        change_percent = ((price_data['current_price'] - float(signal.entry_price)) / float(signal.entry_price)) * 100
                        signal.change_percent = change_percent
                    
                    # Calculate P&L if quantity exists
                    if signal.quantity and signal.entry_price:
                        current_value = price_data['current_price'] * signal.quantity
                        investment_amount = float(signal.entry_price) * signal.quantity
                        pnl = current_value - investment_amount
                        
                        signal.current_value = current_value
                        signal.investment_amount = investment_amount
                        signal.pnl = pnl
                        signal.pnl_percentage = (pnl / investment_amount) * 100 if investment_amount > 0 else 0
                    
                    updated_count += 1
                    logger.debug(f"Updated {signal.symbol}: ₹{price_data['current_price']}")
            
            # Commit all updates
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} signals with Yahoo Finance data")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating admin signals prices: {str(e)}")
            db.session.rollback()
            return 0
    
    def update_realtime_quotes(self):
        """Update realtime_quotes table with Yahoo Finance data"""
        try:
            # Get unique symbols from admin signals
            symbols_result = db.session.query(AdminTradeSignal.symbol).filter_by(status='ACTIVE').distinct().all()
            symbols = [row[0] for row in symbols_result]
            
            if not symbols:
                logger.info("No symbols to update in realtime quotes")
                return 0
            
            # Get prices from Yahoo Finance
            prices = self.get_multiple_prices(symbols)
            
            updated_count = 0
            for symbol, price_data in prices.items():
                # Update or create realtime quote
                quote = RealtimeQuote.query.filter_by(symbol=symbol).first()
                
                if not quote:
                    quote = RealtimeQuote(symbol=symbol)
                    db.session.add(quote)
                
                # Update quote data
                quote.current_price = price_data['current_price']
                quote.open_price = price_data.get('open_price')
                quote.high_price = price_data.get('high_price')
                quote.low_price = price_data.get('low_price')
                quote.close_price = price_data.get('previous_close')
                quote.change_amount = price_data.get('change_amount')
                quote.change_percent = price_data.get('change_percent')
                quote.volume = price_data.get('volume')
                quote.timestamp = datetime.utcnow()
                quote.data_source = 'YAHOO_FINANCE'
                quote.fetch_status = 'SUCCESS'
                
                updated_count += 1
                logger.debug(f"Updated quote for {symbol}: ₹{price_data['current_price']}")
            
            # Commit all updates
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} realtime quotes with Yahoo Finance data")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating realtime quotes: {str(e)}")
            db.session.rollback()
            return 0

# Global service instance
yahoo_service = YahooFinanceService()
