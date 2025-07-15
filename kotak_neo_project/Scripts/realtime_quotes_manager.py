"""
Real-time Quotes Manager
Handles real-time market data fetching and management
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.database import db
from Scripts.models_etf import RealtimeQuote, AdminTradeSignal

logger = logging.getLogger(__name__)

class RealtimeQuotesManager:
    """Manages real-time quotes fetching and storage"""
    
    def __init__(self):
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the real-time quotes manager"""
        if not self.is_running:
            self.is_running = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_scheduler)
            self._thread.daemon = True
            self._thread.start()
            logger.info("Real-time quotes manager started")
    
    def stop(self):
        """Stop the real-time quotes manager"""
        self.is_running = False
        if self._stop_event:
            self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Real-time quotes manager stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while not self._stop_event.is_set():
            try:
                self._fetch_and_store_quotes()
                time.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"Error in quotes scheduler: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _fetch_and_store_quotes(self):
        """Fetch and store quotes for tracked symbols"""
        try:
            # Get unique symbols from admin trade signals
            symbols = db.session.query(AdminTradeSignal.symbol).distinct().all()
            symbols = [s[0] for s in symbols if s[0]]
            
            if not symbols:
                logger.info("No symbols to track")
                return
            
            # For now, store mock quotes since we don't have real API access
            # In production, this would fetch from actual market data API
            for symbol in symbols:
                quote = RealtimeQuote(
                    symbol=symbol,
                    ltp=100.0,  # This would be real price
                    change=0.5,
                    change_percent=0.5,
                    volume=1000,
                    timestamp=datetime.utcnow()
                )
                db.session.add(quote)
            
            db.session.commit()
            logger.info(f"Updated quotes for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            db.session.rollback()

# Global instance
realtime_quotes_manager = RealtimeQuotesManager()

def get_latest_quotes_api(symbols: Optional[List[str]] = None) -> List[Dict]:
    """Get latest quotes for specified symbols"""
    try:
        query = RealtimeQuote.query
        
        if symbols:
            query = query.filter(RealtimeQuote.symbol.in_(symbols))
        
        # Get latest quote for each symbol
        subquery = db.session.query(
            RealtimeQuote.symbol,
            db.func.max(RealtimeQuote.timestamp).label('max_timestamp')
        ).group_by(RealtimeQuote.symbol).subquery()
        
        quotes = query.join(
            subquery,
            (RealtimeQuote.symbol == subquery.c.symbol) &
            (RealtimeQuote.timestamp == subquery.c.max_timestamp)
        ).all()
        
        return [
            {
                'symbol': quote.symbol,
                'ltp': quote.ltp,
                'change': quote.change,
                'change_percent': quote.change_percent,
                'volume': quote.volume,
                'timestamp': quote.timestamp.isoformat()
            }
            for quote in quotes
        ]
        
    except Exception as e:
        logger.error(f"Error getting latest quotes: {e}")
        return []

def force_fetch_quotes():
    """Force immediate quotes fetch"""
    try:
        realtime_quotes_manager._fetch_and_store_quotes()
        return True
    except Exception as e:
        logger.error(f"Error forcing quotes fetch: {e}")
        return False