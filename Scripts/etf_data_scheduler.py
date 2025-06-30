
import schedule
import time
import threading
import logging
from datetime import datetime
from app import app, db
from Scripts.models_etf import ETFSignalTrade
from Scripts.trading_functions import TradingFunctions
from Scripts.session_manager import SessionManager
from Scripts.neo_client import NeoClient
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETFDataScheduler:
    def __init__(self):
        self.trading_functions = TradingFunctions()
        self.session_manager = SessionManager()
        self.neo_client = NeoClient()
        self.client = None
        self.is_running = False
        
        # ETF instruments to track
        self.etf_instruments = [
            {'symbol': 'NIFTYBEES', 'token': '15068'},
            {'symbol': 'GOLDBEES', 'token': '1660'},
            {'symbol': 'BANKBEES', 'token': '34605'},
            {'symbol': 'ITBEES', 'token': '1348'},
            {'symbol': 'JUNIORBEES', 'token': '15081'},
            {'symbol': 'SILVERBEES', 'token': '1659'},
            {'symbol': 'LIQUIDBEES', 'token': '15060'},
            {'symbol': 'PSUBNKBEES', 'token': '34604'},
            {'symbol': 'PVTBNKBEES', 'token': '34603'},
            {'symbol': 'PHARMABEES', 'token': '1347'},
            {'symbol': 'ICICINIFTY', 'token': '1082'},
            {'symbol': 'HDFCNIFTY', 'token': '1073'},
            {'symbol': 'UTINIFTY', 'token': '1066'},
            {'symbol': 'LICNFNXT50', 'token': '1320'},
            {'symbol': 'ICICIB22', 'token': '1299'},
            {'symbol': 'HDFCMFGETF', 'token': '1310'},
            {'symbol': 'KOTAKNIFTY', 'token': '1154'},
            {'symbol': 'RELIANCE', 'token': '2885'},
            {'symbol': 'TCS', 'token': '11536'},
            {'symbol': 'INFY', 'token': '1594'},
        ]

    def initialize_client(self):
        """Initialize Kotak Neo client with stored session"""
        try:
            # Get stored session data
            session_data = self.session_manager.get_session('default_user')
            if not session_data:
                logger.error("No stored session found. Please login first.")
                return False

            # Initialize client with stored tokens
            self.client = self.neo_client.initialize_client_with_tokens(
                session_data.get('access_token'),
                session_data.get('session_token'),
                session_data.get('sid')
            )

            if self.client:
                # Validate session
                if self.neo_client.validate_session(self.client):
                    logger.info("✅ Client initialized successfully")
                    return True
                else:
                    logger.error("❌ Session validation failed")
                    return False
            else:
                logger.error("❌ Failed to initialize client")
                return False

        except Exception as e:
            logger.error(f"❌ Error initializing client: {str(e)}")
            return False

    def fetch_etf_quotes(self):
        """Fetch live quotes for all ETF instruments"""
        try:
            if not self.client:
                if not self.initialize_client():
                    logger.error("Cannot fetch quotes - client not initialized")
                    return

            logger.info(f"🔄 Fetching quotes for {len(self.etf_instruments)} ETF instruments...")

            # Extract tokens for quote request
            instrument_tokens = [etf['token'] for etf in self.etf_instruments]

            # Get quotes from Kotak Neo API
            quote_data = {
                'instrument_tokens': instrument_tokens,
                'quote_type': None,
                'is_index': False
            }

            quotes_response = self.trading_functions.get_quotes(self.client, quote_data)

            if quotes_response.get('success'):
                quotes = quotes_response.get('data', {})
                logger.info(f"✅ Received quotes for {len(quotes)} instruments")
                
                # Update database with new quotes
                self.update_etf_database(quotes)
            else:
                logger.error(f"❌ Failed to get quotes: {quotes_response.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Error fetching ETF quotes: {str(e)}")

    def update_etf_database(self, quotes):
        """Update ETF signal trades with current market prices"""
        try:
            with app.app_context():
                updated_count = 0
                
                for token, quote_info in quotes.items():
                    # Find corresponding ETF symbol
                    etf_symbol = None
                    for etf in self.etf_instruments:
                        if etf['token'] == token:
                            etf_symbol = etf['symbol']
                            break
                    
                    if not etf_symbol:
                        continue

                    # Extract quote data
                    current_price = float(quote_info.get('last_traded_price', 0))
                    change_percent = float(quote_info.get('change_percent', 0))

                    if current_price <= 0:
                        continue

                    # Update all active ETF signal trades for this symbol
                    etf_trades = ETFSignalTrade.query.filter_by(
                        symbol=etf_symbol,
                        status='ACTIVE'
                    ).all()

                    for trade in etf_trades:
                        # Update current price
                        trade.current_price = current_price
                        trade.change_pct = f"{change_percent:.2f}%"
                        trade.last_price_update = datetime.utcnow()
                        
                        # Recalculate P&L
                        trade.calculate_pnl()
                        
                        updated_count += 1
                        
                        logger.debug(f"Updated {etf_symbol}: Price={current_price}, Change={change_percent}%")

                # Commit all updates
                db.session.commit()
                logger.info(f"✅ Updated {updated_count} ETF trades in database")

        except Exception as e:
            logger.error(f"❌ Error updating ETF database: {str(e)}")
            db.session.rollback()

    def start_scheduler(self):
        """Start the background scheduler"""
        try:
            if self.is_running:
                logger.warning("Scheduler is already running")
                return

            # Schedule to run every 5 minutes
            schedule.every(5).minutes.do(self.fetch_etf_quotes)
            
            # Run immediately on start
            self.fetch_etf_quotes()
            
            self.is_running = True
            logger.info("🚀 ETF Data Scheduler started - fetching quotes every 5 minutes")

            # Run scheduler in background thread
            def run_scheduler():
                while self.is_running:
                    schedule.run_pending()
                    time.sleep(30)  # Check every 30 seconds

            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()

        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {str(e)}")

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 ETF Data Scheduler stopped")

# Global scheduler instance
etf_scheduler = ETFDataScheduler()

def start_etf_data_scheduler():
    """Function to start the ETF data scheduler"""
    etf_scheduler.start_scheduler()

def stop_etf_data_scheduler():
    """Function to stop the ETF data scheduler"""
    etf_scheduler.stop_scheduler()
