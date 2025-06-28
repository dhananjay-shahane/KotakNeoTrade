
#!/usr/bin/env python3
"""
Setup script for real-time ETF trading system
Run this to initialize the system with real-time data tracking
"""

import logging
from app import app, db
from Scripts.create_initial_etf_trades import create_initial_etf_trades
from Scripts.etf_data_scheduler import start_etf_data_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_real_time_etf_system():
    """Setup the complete real-time ETF system"""
    try:
        with app.app_context():
            # 1. Create database tables
            logger.info("🏗️ Creating database tables...")
            db.create_all()
            
            # 2. Create initial ETF trades
            logger.info("📊 Creating initial ETF trades...")
            trades_count = create_initial_etf_trades()
            
            if trades_count > 0:
                logger.info(f"✅ Created {trades_count} initial ETF trades")
                
                # 3. Start the data scheduler
                logger.info("🚀 Starting ETF data scheduler...")
                start_etf_data_scheduler()
                
                logger.info("✅ Real-time ETF system setup complete!")
                logger.info("📈 The system will now fetch live quotes every 5 minutes")
                logger.info("🌐 Access the ETF signals page to see real-time data")
                
                return True
            else:
                logger.error("❌ Failed to create initial ETF trades")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error setting up real-time ETF system: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_real_time_etf_system()
    if success:
        print("\n🎉 Real-time ETF system is ready!")
        print("Visit the ETF Signals page to see live data updates every 5 minutes.")
    else:
        print("\n❌ Setup failed. Please check the logs for errors.")
