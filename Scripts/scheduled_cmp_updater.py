#!/usr/bin/env python3
"""
Scheduled CMP Updater - Automated background service for updating CMP values
Runs continuously and updates admin_trade_signals table at regular intervals
"""

import time
import schedule
import logging
from datetime import datetime
import threading
import signal
import sys
from google_finance_cmp_updater import GoogleFinanceCMPUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_cmp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ScheduledCMPUpdater:
    """Scheduled service for automatic CMP updates"""
    
    def __init__(self, update_interval_minutes=5):
        self.update_interval = update_interval_minutes
        self.updater = GoogleFinanceCMPUpdater()
        self.running = False
        self.scheduler_thread = None
        
    def update_cmp_job(self):
        """Job function to update CMP values"""
        try:
            logging.info(f"🔄 Starting scheduled CMP update at {datetime.now()}")
            result = self.updater.update_all_symbols()
            
            if result['success']:
                logging.info(f"✅ Scheduled update completed: {result['updated_count']} records updated in {result['duration']:.2f}s")
            else:
                logging.error(f"❌ Scheduled update failed: {result['message']}")
                
        except Exception as e:
            logging.error(f"❌ Error in scheduled CMP update: {str(e)}")
    
    def start_scheduler(self):
        """Start the scheduled CMP updater"""
        logging.info(f"🚀 Starting scheduled CMP updater (every {self.update_interval} minutes)")
        
        # Schedule the job
        schedule.every(self.update_interval).minutes.do(self.update_cmp_job)
        
        # Run initial update
        self.update_cmp_job()
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logging.info(f"✅ Scheduled CMP updater started (every {self.update_interval} minutes)")
        
    def stop_scheduler(self):
        """Stop the scheduled CMP updater"""
        logging.info("🛑 Stopping scheduled CMP updater...")
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        logging.info("✅ Scheduled CMP updater stopped")

# Global scheduler instance
scheduler_instance = None

def signal_handler(signum, frame):
    """Handle termination signals"""
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    if scheduler_instance:
        scheduler_instance.stop_scheduler()
    sys.exit(0)

def start_scheduled_cmp_updater(interval_minutes=5):
    """Start the scheduled CMP updater service"""
    global scheduler_instance
    
    if scheduler_instance and scheduler_instance.running:
        logging.warning("Scheduled CMP updater is already running")
        return scheduler_instance
    
    scheduler_instance = ScheduledCMPUpdater(interval_minutes)
    scheduler_instance.start_scheduler()
    return scheduler_instance

def stop_scheduled_cmp_updater():
    """Stop the scheduled CMP updater service"""
    global scheduler_instance
    
    if scheduler_instance:
        scheduler_instance.stop_scheduler()
        scheduler_instance = None
    else:
        logging.warning("No scheduled CMP updater running")

def get_scheduler_status():
    """Get current scheduler status"""
    if scheduler_instance and scheduler_instance.running:
        return {
            'running': True,
            'interval_minutes': scheduler_instance.update_interval,
            'message': f'Scheduled CMP updater running (every {scheduler_instance.update_interval} minutes)'
        }
    else:
        return {
            'running': False,
            'interval_minutes': 0,
            'message': 'Scheduled CMP updater not running'
        }

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scheduled CMP Updater Service')
    parser.add_argument('--interval', type=int, default=5, help='Update interval in minutes (default: 5)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon service')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Scheduled CMP Updater Service")
    print("=" * 50)
    print(f"Update interval: {args.interval} minutes")
    print(f"Daemon mode: {args.daemon}")
    print("=" * 50)
    
    # Start the scheduler
    scheduler = start_scheduled_cmp_updater(args.interval)
    
    if args.daemon:
        # Run as daemon
        logging.info("Running in daemon mode. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        # Interactive mode
        print("\nScheduled CMP updater is running...")
        print("Commands:")
        print("  'status' - Show status")
        print("  'update' - Force update now")
        print("  'stop' or 'quit' - Stop service")
        print("  'help' - Show this help")
        
        try:
            while scheduler.running:
                try:
                    command = input("\n> ").strip().lower()
                    
                    if command in ['stop', 'quit', 'exit']:
                        break
                    elif command == 'status':
                        status = get_scheduler_status()
                        print(f"Status: {status['message']}")
                    elif command == 'update':
                        print("Forcing CMP update...")
                        scheduler.update_cmp_job()
                    elif command == 'help':
                        print("Commands: status, update, stop, help")
                    elif command:
                        print(f"Unknown command: {command}")
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            pass
    
    # Clean shutdown
    stop_scheduled_cmp_updater()
    print("\n✅ Scheduled CMP updater stopped")

if __name__ == "__main__":
    main()