"""
Fallback Data Service for Trading Signals
Provides sample trading data when external database is not available
This ensures the application can still demonstrate functionality
"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class FallbackDataService:
    """Service to provide sample trading data when database is unavailable"""
    
    def __init__(self):
        self.sample_symbols = [
            'GOLDBEES', 'NIFTYBEES', 'BANKBEES', 'JUNIORBEES', 'SETFGOLD',
            'LIQUIDBEES', 'PVTBANKG', 'ITBEES', 'PHARMABES', 'FMCGBEES'
        ]
    
    def get_sample_etf_signals(self) -> List[Dict]:
        """Generate sample ETF signals data for demonstration"""
        signals = []
        
        for i, symbol in enumerate(self.sample_symbols[:10]):
            # Generate realistic sample data
            entry_price = round(random.uniform(50.0, 500.0), 2)
            current_price = round(entry_price * random.uniform(0.9, 1.15), 2)
            quantity = random.randint(10, 100)
            investment = entry_price * quantity
            current_value = current_price * quantity
            pnl = current_value - investment
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            # Create sample entry date (last 30 days)
            entry_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            
            signal = {
                'trade_signal_id': i + 1,
                'etf': symbol,
                'symbol': symbol,
                'thirty': round(current_price * 0.98, 2),
                'dh': f"{random.uniform(-5, 15):.2f}%",
                'seven': round(current_price * 0.995, 2), 
                'ch': f"{random.uniform(-2, 8):.2f}%",
                'date': entry_date,
                'qty': quantity,
                'ep': entry_price,
                'cmp': current_price,
                'chan': f"{pnl_percent:.2f}%",
                'inv': round(investment, 2),
                'tp': round(entry_price * 1.1, 2),
                'tpr': round(investment * 0.1, 2),
                'tva': round(current_value, 2),
                'cpl': round(pnl, 2),
                'pl': round(pnl, 2),
                'pos': 1,  # LONG position
                'status': 'ACTIVE',
                'ed': entry_date,
                'exp': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'pr': f"{entry_price:.2f}-{entry_price * 1.2:.2f}",
                'pp': round(pnl_percent, 2),
                'iv': round(random.uniform(15, 35), 2),
                'ip': round(random.uniform(-5, 10), 2),
                'created_at': entry_date
            }
            signals.append(signal)
        
        logger.info(f"Generated {len(signals)} sample ETF signals for demonstration")
        return signals

def get_etf_signals_data_json():
    """Get ETF signals data - fallback version when database is unavailable"""
    try:
        # Try to get real data first
        from Scripts.external_db_service import ExternalDBService
        db_service = ExternalDBService()
        real_data = db_service.get_admin_trade_signals()
        
        if real_data:
            logger.info("Using real database data")
            return {
                'success': True,
                'data': real_data,
                'count': len(real_data),
                'source': 'database'
            }
    except Exception as e:
        logger.warning(f"Database unavailable: {e}")
    
    # Use fallback data for demonstration
    fallback_service = FallbackDataService()
    sample_data = fallback_service.get_sample_etf_signals()
    
    return {
        'success': True,
        'data': sample_data,
        'count': len(sample_data),
        'source': 'fallback',
        'message': 'Using sample data for demonstration. Database connection required for real trading data.'
    }

def get_basic_trade_signals_data_json():
    """Get basic trade signals data - fallback version"""
    return get_etf_signals_data_json()