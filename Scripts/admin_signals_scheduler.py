"""
Admin Trade Signals Scheduler - Automatic Kotak Neo quotes data updates
Updates admin_trade_signals table with real-time market data every 5 minutes
"""
import schedule
import time
import threading
import logging
from datetime import datetime
from app import app, db
from Scripts.models_etf import AdminTradeSignal, KotakNeoQuote
from Scripts.trading_functions import TradingFunctions

logger = logging.getLogger(__name__)

class AdminSignalsScheduler:
    """Scheduler for updating admin trade signals with Kotak Neo quotes data"""
    
    def __init__(self):
        self.scheduler_thread = None
        self.is_running = False
        self.trading_functions = None
        
    def initialize_trading_client(self):
        """Initialize trading functions client"""
        try:
            self.trading_functions = TradingFunctions()
            logger.info("✅ Trading functions initialized for admin signals scheduler")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize trading functions: {str(e)}")
            return False
    
    def update_admin_signals_with_quotes(self):
        """Update admin trade signals with latest Kotak Neo quotes data"""
        try:
            with app.app_context():
                # Get all active admin trade signals
                active_signals = AdminTradeSignal.query.filter_by(status='ACTIVE').all()
                
                if not active_signals:
                    logger.info("📊 No active admin trade signals found")
                    return
                
                logger.info(f"🔄 Updating {len(active_signals)} admin trade signals with Kotak Neo data")
                
                updated_count = 0
                symbols_processed = []
                
                for signal in active_signals:
                    try:
                        # Get live quote for this symbol
                        if self.trading_functions:
                            quote_data = self.trading_functions.get_live_quotes([signal.symbol])
                            
                            if quote_data and len(quote_data) > 0:
                                quote = quote_data[0]
                                
                                # Update signal with live market data
                                signal.current_price = float(quote.get('ltp', signal.current_price or signal.entry_price))
                                signal.last_update_time = datetime.now()
                                
                                # Store comprehensive quote data in KotakNeoQuote table
                                kotak_quote = KotakNeoQuote(
                                    symbol=signal.symbol,
                                    trading_symbol=signal.trading_symbol or signal.symbol,
                                    token=quote.get('token'),
                                    exchange=signal.exchange or 'NSE',
                                    ltp=float(quote.get('ltp', 0)),
                                    open_price=float(quote.get('open', 0)),
                                    high_price=float(quote.get('high', 0)),
                                    low_price=float(quote.get('low', 0)),
                                    close_price=float(quote.get('close', 0)),
                                    net_change=float(quote.get('netChng', 0)),
                                    percentage_change=float(quote.get('prcntChng', 0)),
                                    volume=int(quote.get('vol', 0)),
                                    bid_price=float(quote.get('bid', 0)),
                                    ask_price=float(quote.get('ask', 0)),
                                    timestamp=datetime.now()
                                )
                                
                                # Check if quote already exists for this symbol today
                                existing_quote = KotakNeoQuote.query.filter_by(
                                    symbol=signal.symbol
                                ).filter(
                                    KotakNeoQuote.timestamp >= datetime.now().date()
                                ).order_by(KotakNeoQuote.timestamp.desc()).first()
                                
                                if existing_quote:
                                    # Update existing quote
                                    existing_quote.ltp = kotak_quote.ltp
                                    existing_quote.open_price = kotak_quote.open_price
                                    existing_quote.high_price = kotak_quote.high_price
                                    existing_quote.low_price = kotak_quote.low_price
                                    existing_quote.net_change = kotak_quote.net_change
                                    existing_quote.percentage_change = kotak_quote.percentage_change
                                    existing_quote.volume = kotak_quote.volume
                                    existing_quote.bid_price = kotak_quote.bid_price
                                    existing_quote.ask_price = kotak_quote.ask_price
                                    existing_quote.timestamp = datetime.now()
                                else:
                                    # Add new quote
                                    db.session.add(kotak_quote)
                                
                                updated_count += 1
                                symbols_processed.append(signal.symbol)
                                
                                logger.debug(f"✅ Updated {signal.symbol}: ₹{signal.current_price:.2f}")
                            else:
                                logger.warning(f"⚠️ No quote data received for {signal.symbol}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error updating signal {signal.symbol}: {str(e)}")
                        continue
                
                # Commit all updates
                db.session.commit()
                
                logger.info(f"✅ Admin signals update completed: {updated_count}/{len(active_signals)} signals updated")
                logger.info(f"📈 Symbols processed: {', '.join(symbols_processed)}")
                
        except Exception as e:
            logger.error(f"❌ Error in admin signals scheduler: {str(e)}")
            db.session.rollback()
    
    def scheduled_update_job(self):
        """Job function to be run by scheduler"""
        logger.info("🕐 Starting scheduled admin signals update...")
        start_time = datetime.now()
        
        self.update_admin_signals_with_quotes()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"⏱️ Admin signals update completed in {duration:.2f} seconds")
    
    def start_scheduler(self):
        """Start the 5-minute scheduler"""
        if self.is_running:
            logger.warning("⚠️ Admin signals scheduler is already running")
            return
        
        # Initialize trading client
        if not self.initialize_trading_client():
            logger.error("❌ Cannot start scheduler - trading client initialization failed")
            return
        
        # Schedule the job every 5 minutes
        schedule.every(5).minutes.do(self.scheduled_update_job)
        
        # Run initial update
        logger.info("🚀 Running initial admin signals update...")
        self.scheduled_update_job()
        
        def run_scheduler():
            """Background thread function for scheduler"""
            self.is_running = True
            logger.info("✅ Admin signals scheduler started - updating every 5 minutes")
            
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    logger.error(f"❌ Scheduler error: {str(e)}")
                    time.sleep(30)  # Wait 30 seconds on error
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("🔄 Admin signals scheduler initialized successfully")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("⚠️ Admin signals scheduler is not running")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("🛑 Admin signals scheduler stopped")

# Global scheduler instance
admin_signals_scheduler = AdminSignalsScheduler()

def start_admin_signals_scheduler():
    """Function to start the admin signals scheduler"""
    admin_signals_scheduler.start_scheduler()

def stop_admin_signals_scheduler():
    """Function to stop the admin signals scheduler"""
    admin_signals_scheduler.stop_scheduler()

def get_scheduler_status():
    """Get current scheduler status"""
    return {
        'is_running': admin_signals_scheduler.is_running,
        'thread_alive': admin_signals_scheduler.scheduler_thread.is_alive() if admin_signals_scheduler.scheduler_thread else False,
        'trading_client_initialized': admin_signals_scheduler.trading_functions is not None
    }

if __name__ == "__main__":
    # For testing the scheduler directly
    print("🧪 Testing Admin Signals Scheduler...")
    start_admin_signals_scheduler()
    
    try:
        # Keep running for testing
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        stop_admin_signals_scheduler()