
import schedule
import time
import threading
import logging
from datetime import datetime
from yahoo_finance_service import yahoo_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooFinanceScheduler:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
    
    def update_prices(self):
        """Update prices from Yahoo Finance"""
        try:
            logger.info("🔄 Starting Yahoo Finance price update...")
            
            # Update admin signals
            signals_updated = yahoo_service.update_admin_signals_prices()
            
            # Update realtime quotes
            quotes_updated = yahoo_service.update_realtime_quotes()
            
            logger.info(f"✅ Updated {signals_updated} signals and {quotes_updated} quotes from Yahoo Finance")
            
        except Exception as e:
            logger.error(f"❌ Error in Yahoo Finance update: {str(e)}")
    
    def start_scheduler(self):
        """Start the background scheduler"""
        try:
            if self.is_running:
                logger.warning("Yahoo Finance scheduler is already running")
                return
            
            # Schedule updates every 5 minutes during market hours
            schedule.every(5).minutes.do(self.update_prices)
            
            # Run immediately on start
            self.update_prices()
            
            self.is_running = True
            logger.info("🚀 Yahoo Finance Scheduler started - updating prices every 5 minutes")
            
            # Run scheduler in background thread
            def run_scheduler():
                while self.is_running:
                    schedule.run_pending()
                    time.sleep(30)  # Check every 30 seconds
            
            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Error starting Yahoo Finance scheduler: {str(e)}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 Yahoo Finance Scheduler stopped")
    
    def force_update(self):
        """Force an immediate update"""
        logger.info("🔄 Force updating prices from Yahoo Finance...")
        self.update_prices()

# Global scheduler instance
yahoo_scheduler = YahooFinanceScheduler()

def start_yahoo_scheduler():
    """Function to start the Yahoo Finance scheduler"""
    yahoo_scheduler.start_scheduler()

def stop_yahoo_scheduler():
    """Function to stop the Yahoo Finance scheduler"""
    yahoo_scheduler.stop_scheduler()

def force_yahoo_update():
    """Function to force immediate Yahoo Finance update"""
    yahoo_scheduler.force_update()
