#!/usr/bin/env python3
"""
Google Finance Scheduler - Automatic CMP updates every 5 minutes
Runs in background to keep ETF prices updated with live Google Finance data
"""

import threading
import time
import logging
import requests
from datetime import datetime
from Scripts.google_finance_cmp_updater import GoogleFinanceCMPUpdater

class GoogleFinanceScheduler:
    """Background scheduler for Google Finance CMP updates"""
    
    def __init__(self):
        self.scheduler_thread = None
        self.running = False
        self.updater = GoogleFinanceCMPUpdater()
        self.update_interval = 300  # 5 minutes in seconds
        
    def start_scheduler(self):
        """Start the 5-minute scheduler"""
        if self.running:
            logging.info("⚡ Google Finance scheduler already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logging.info("🚀 Google Finance scheduler started - updating every 5 minutes")
        
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.running:
            return
            
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
        logging.info("⏹️ Google Finance scheduler stopped")
        
    def _run_scheduler(self):
        """Background thread function for scheduler"""
        while self.running:
            try:
                # Wait for the interval (check every 10 seconds for stop signal)
                for _ in range(0, self.update_interval, 10):
                    if not self.running:
                        return
                    time.sleep(10)
                
                if self.running:
                    self._update_prices()
                    
            except Exception as e:
                logging.error(f"❌ Scheduler error: {e}")
                # Wait a bit before retrying
                time.sleep(60)
                
    def _update_prices(self):
        """Update CMP prices using Google Finance"""
        try:
            start_time = datetime.now()
            logging.info("🔄 Scheduled Google Finance update started")
            
            # Call the updater
            result = self.updater.update_all_symbols()
            
            if result.get('success'):
                duration = result.get('duration', 0)
                updated_count = result.get('updated_count', 0)
                logging.info(f"✅ Scheduled update completed: {updated_count} records updated in {duration:.1f}s")
            else:
                logging.warning(f"⚠️ Scheduled update had issues: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logging.error(f"❌ Error in scheduled update: {e}")

# Global scheduler instance
_scheduler_instance = None

def start_google_finance_scheduler():
    """Start the Google Finance scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = GoogleFinanceScheduler()
    
    _scheduler_instance.start_scheduler()
    return _scheduler_instance

def stop_google_finance_scheduler():
    """Stop the Google Finance scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop_scheduler()

def get_scheduler_status():
    """Get current scheduler status"""
    global _scheduler_instance
    
    if _scheduler_instance and _scheduler_instance.running:
        return {
            'status': 'running',
            'update_interval': _scheduler_instance.update_interval,
            'message': 'Google Finance scheduler is running'
        }
    else:
        return {
            'status': 'stopped',
            'update_interval': 0,
            'message': 'Google Finance scheduler is not running'
        }

def force_update_now():
    """Force an immediate update"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance._update_prices()
        return True
    return False

if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(level=logging.INFO)
    scheduler = start_google_finance_scheduler()
    
    try:
        # Run for testing
        time.sleep(320)  # Run for about 5 minutes to test one cycle
    except KeyboardInterrupt:
        stop_google_finance_scheduler()
        print("Scheduler stopped")