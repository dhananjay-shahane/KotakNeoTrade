"""
User Deals Service for Portfolio Statistics
Provides deal counts, symbol data, and pie chart information
"""
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional
import os
from collections import Counter

logger = logging.getLogger(__name__)

class UserDealsService:
    """Service for fetching user deals statistics"""
    
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL", 
                                   "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db")
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def get_deals_statistics(self, user_id: int = 1) -> Dict:
        """
        Get comprehensive deals statistics for portfolio page
        Args:
            user_id: User ID (default 1)
        Returns:
            Dictionary with deals statistics and chart data
        """
        try:
            conn = self.get_connection()
            if not conn:
                return self._empty_stats()
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Query to get all user deals
            query = """
                SELECT trade_signal_id, symbol, qty, date, ep, pos, ed, status
                FROM user_deals 
                WHERE user_id = %s
                ORDER BY date DESC
            """
            
            cursor.execute(query, (user_id,))
            deals = cursor.fetchall()
            
            if not deals:
                return self._empty_stats()
            
            # Calculate statistics
            total_deals = len(deals)
            active_deals = len([d for d in deals if d['status'] == 'ACTIVE'])
            closed_deals = len([d for d in deals if d['status'] == 'CLOSED'])
            
            # Get unique symbols
            symbols = list(set([d['symbol'] for d in deals]))
            
            # Symbol distribution for pie chart
            symbol_counts = Counter([d['symbol'] for d in deals])
            
            # Prepare chart data
            chart_data = {
                'labels': list(symbol_counts.keys()),
                'data': list(symbol_counts.values()),
                'colors': self._generate_colors(len(symbol_counts))
            }
            
            # Status distribution for pie chart
            status_data = {
                'labels': ['Active Deals', 'Closed Deals'],
                'data': [active_deals, closed_deals],
                'colors': ['#10B981', '#EF4444']  # Green for active, red for closed
            }
            
            conn.close()
            
            return {
                'total_deals': total_deals,
                'active_deals': active_deals,
                'closed_deals': closed_deals,
                'symbols': symbols[:10],  # Show top 10 symbols
                'symbol_chart_data': chart_data,
                'status_chart_data': status_data,
                'deals_list': [dict(deal) for deal in deals[:5]]  # Show last 5 deals
            }
            
        except Exception as e:
            logger.error(f"Error getting deals statistics: {e}")
            return self._empty_stats()
    
    def _empty_stats(self) -> Dict:
        """Return empty statistics structure"""
        return {
            'total_deals': 0,
            'active_deals': 0,
            'closed_deals': 0,
            'symbols': [],
            'symbol_chart_data': {'labels': [], 'data': [], 'colors': []},
            'status_chart_data': {'labels': [], 'data': [], 'colors': []},
            'deals_list': []
        }
    
    def _generate_colors(self, count: int) -> List[str]:
        """Generate colors for pie chart"""
        colors = [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
            '#06B6D4', '#EC4899', '#84CC16', '#F97316', '#6366F1'
        ]
        return (colors * ((count // len(colors)) + 1))[:count]