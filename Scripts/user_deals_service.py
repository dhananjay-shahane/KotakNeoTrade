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
        # Use the same external database connection as deals API
        self.db_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db"
    
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
            
            # Query to get all user deals - using same structure as working deals API
            query = """
                SELECT trade_signal_id, symbol, qty, created_at, ep, pos, ed, status
                FROM public.user_deals 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (user_id,))
            deals = cursor.fetchall()
            
            if not deals:
                return self._empty_stats()
            
            # Calculate statistics with null checks
            total_deals = len(deals)
            active_deals = len([d for d in deals if d['status'] == 'ACTIVE'])
            closed_deals = len([d for d in deals if d['status'] == 'CLOSED'])
            
            # Calculate total investment and P&L
            total_investment = 0
            total_current_value = 0
            
            for deal in deals:
                if deal['ep'] is not None and deal['qty'] is not None:
                    ep_value = float(deal['ep'])
                    qty_value = int(deal['qty'])
                    investment = ep_value * qty_value
                    total_investment += investment
                    
                    # Mock current value with 5% gain
                    current_value = investment * 1.05
                    total_current_value += current_value
            
            total_pnl = total_current_value - total_investment
            
            # Get unique symbols
            symbols = list(set([d['symbol'] for d in deals if d['symbol']]))
            
            # Symbol distribution for pie chart
            symbol_counts = Counter([d['symbol'] for d in deals if d['symbol']])
            
            # Prepare chart data for symbols
            chart_data = {
                'labels': list(symbol_counts.keys()),
                'data': list(symbol_counts.values()),
                'colors': self._generate_colors(len(symbol_counts))
            }
            
            # Profit/Loss distribution for pie chart
            if total_investment > 0:
                pnl_data = {
                    'labels': ['Investment', 'Profit/Loss'],
                    'data': [round(total_investment, 2), round(abs(total_pnl), 2)],
                    'colors': ['#3B82F6', '#10B981' if total_pnl >= 0 else '#EF4444']
                }
            else:
                pnl_data = {
                    'labels': ['No Data'],
                    'data': [1],
                    'colors': ['#95a5a6']
                }
            
            conn.close()
            
            return {
                'total_deals': total_deals,
                'active_deals': active_deals,
                'closed_deals': closed_deals,
                'total_investment': round(total_investment, 2),
                'total_current_value': round(total_current_value, 2),
                'total_pnl': round(total_pnl, 2),
                'symbols': symbols[:10],  # Show top 10 symbols
                'symbol_chart_data': chart_data,
                'status_chart_data': pnl_data,  # Changed to show P&L instead of status
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
            'total_investment': 0,
            'total_current_value': 0,
            'total_pnl': 0,
            'symbols': [],
            'symbol_chart_data': {'labels': [], 'data': [], 'colors': []},
            'status_chart_data': {'labels': ['No Data'], 'data': [1], 'colors': ['#95a5a6']},
            'deals_list': []
        }
    
    def _generate_colors(self, count: int) -> List[str]:
        """Generate colors for pie chart"""
        colors = [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
            '#06B6D4', '#EC4899', '#84CC16', '#F97316', '#6366F1'
        ]
        return (colors * ((count // len(colors)) + 1))[:count]
    
    def get_symbol_details(self, user_id: int, symbol: str) -> Dict:
        """
        Get detailed information for a specific symbol
        Args:
            user_id: User ID
            symbol: Trading symbol
        Returns:
            Dictionary with symbol details
        """
        try:
            conn = self.get_connection()
            if not conn:
                return {'error': 'Database connection failed'}
            
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Query to get symbol-specific deals - using same structure as working deals API
            query = """
                SELECT trade_signal_id, symbol, qty, created_at, ep, pos, ed, status
                FROM public.user_deals 
                WHERE user_id = %s AND symbol = %s
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (user_id, symbol))
            deals = cursor.fetchall()
            
            if not deals:
                conn.close()
                return {'error': 'No deals found for this symbol'}
            
            # Calculate totals for this symbol with null checks
            total_investment = 0
            total_quantity = 0
            valid_deals = []
            
            for deal in deals:
                if deal['ep'] is not None and deal['qty'] is not None:
                    ep_value = float(deal['ep'])
                    qty_value = int(deal['qty'])
                    total_investment += ep_value * qty_value
                    total_quantity += qty_value
                    valid_deals.append(deal)
            
            if not valid_deals:
                conn.close()
                return {'error': 'No valid deals with price data found for this symbol'}
            
            # Mock CMP for calculation (replace with real data source)
            avg_entry_price = total_investment / total_quantity if total_quantity > 0 else 0
            cmp = avg_entry_price * 1.05  # Assume 5% gain for demo
            current_value = cmp * total_quantity
            profit_loss = current_value - total_investment
            profit_loss_percentage = (profit_loss / total_investment) * 100 if total_investment > 0 else 0
            
            # Format deals for display
            formatted_deals = []
            for deal in valid_deals:
                ep_value = float(deal['ep']) if deal['ep'] is not None else 0
                qty_value = int(deal['qty']) if deal['qty'] is not None else 0
                
                formatted_deals.append({
                    'date': deal['created_at'].strftime('%Y-%m-%d') if deal['created_at'] else '--',
                    'entry_price': ep_value,
                    'qty': qty_value,
                    'investment': ep_value * qty_value,
                    'current_value': cmp * qty_value,
                    'status': deal['status'] or 'UNKNOWN'
                })
            
            conn.close()
            
            return {
                'symbol': symbol,
                'cmp': round(cmp, 2),
                'total_investment': round(total_investment, 2),
                'current_value': round(current_value, 2),
                'profit_loss': round(profit_loss, 2),
                'profit_loss_percentage': round(profit_loss_percentage, 2),
                'total_quantity': total_quantity,
                'deals': formatted_deals
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol details for {symbol}: {e}")
            return {'error': str(e)}