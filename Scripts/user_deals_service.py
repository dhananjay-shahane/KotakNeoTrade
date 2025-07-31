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
        # Use centralized database configuration
        from config.database_config import get_database_url
        self.db_url = get_database_url()

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

            # Query to get all user deals with proper fields
            query = """
                SELECT trade_signal_id, symbol, qty, created_at, ep, pos, ed, status
                FROM public.user_deals 
                WHERE user_id = %s AND symbol IS NOT NULL AND symbol != ''
                ORDER BY created_at DESC
            """

            cursor.execute(query, (user_id,))
            deals = cursor.fetchall()

            if not deals:
                return self._empty_stats()

            # Calculate statistics with only real data
            total_deals = len(deals)
            active_deals = len([d for d in deals if d['status'] == 'ACTIVE'])
            closed_deals = len([d for d in deals if d['status'] == 'CLOSED'])

            # Calculate total investment and P&L using only real data
            total_investment = 0
            total_current_value = 0

            for deal in deals:
                try:
                    # Only process deals with valid entry price and quantity
                    ep_value = deal.get('ep')
                    qty_value = deal.get('qty')

                    if ep_value is not None and qty_value is not None:
                        ep_value = float(ep_value)
                        qty_value = int(qty_value)

                        if ep_value > 0 and qty_value > 0:
                            investment = ep_value * qty_value
                            total_investment += investment

                            # For current value, use entry price if CMP not available
                            # This gives realistic portfolio value without fake data
                            current_value = investment  # Conservative approach
                            total_current_value += current_value

                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing deal: {e}")
                    continue

            total_pnl = total_current_value - total_investment

            # Get unique symbols from real data only
            symbols = list(set([d['symbol'] for d in deals if d['symbol']]))

            # Symbol distribution for pie chart - real data only
            symbol_counts = Counter([d['symbol'] for d in deals if d['symbol']])

            # Prepare chart data for symbols
            chart_data = {
                'labels': list(symbol_counts.keys()),
                'data': list(symbol_counts.values()),
                'colors': self._generate_colors(len(symbol_counts))
            }

            # Investment vs P&L chart with real data
            if total_investment > 0:
                pnl_data = {
                    'labels': ['Investment', 'P&L'],
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
                'status_chart_data': pnl_data,
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
        Get detailed information for a specific symbol using only real data
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

            # Query to get symbol-specific deals
            query = """
                SELECT trade_signal_id, symbol, qty, created_at, ep, pos, ed, status
                FROM public.user_deals 
                WHERE user_id = %s AND symbol = %s AND ep IS NOT NULL AND qty IS NOT NULL
                ORDER BY created_at DESC
            """

            cursor.execute(query, (user_id, symbol))
            deals = cursor.fetchall()

            if not deals:
                conn.close()
                return {'error': 'No deals found for this symbol'}

            # Calculate totals for this symbol using only real data
            total_investment = 0
            total_quantity = 0
            valid_deals = []

            for deal in deals:
                try:
                    ep_value = float(deal.get('ep', 0))
                    qty_value = int(deal.get('qty', 0))

                    if ep_value > 0 and qty_value > 0:
                        total_investment += ep_value * qty_value
                        total_quantity += qty_value
                        valid_deals.append(deal)

                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing deal for symbol {symbol}: {e}")
                    continue

            if not valid_deals:
                conn.close()
                return {'error': 'No valid deals with price data found for this symbol'}

            # Calculate metrics using real data only
            if total_quantity > 0 and total_investment > 0:
                avg_entry_price = total_investment / total_quantity
                # Use entry price as CMP since we don't have live market data
                cmp = avg_entry_price
                current_value = cmp * total_quantity
                profit_loss = current_value - total_investment  # Will be 0 without live data
                profit_loss_percentage = (profit_loss / total_investment) * 100 if total_investment > 0 else 0
            else:
                avg_entry_price = 0
                cmp = 0
                current_value = 0
                profit_loss = 0
                profit_loss_percentage = 0

            # Format deals for display with real data only
            formatted_deals = []
            for deal in valid_deals:
                try:
                    ep_value = float(deal.get('ep', 0))
                    qty_value = int(deal.get('qty', 0))

                    if ep_value > 0 and qty_value > 0:
                        formatted_deals.append({
                            'date': deal['created_at'].strftime('%Y-%m-%d') if deal.get('created_at') else '--',
                            'entry_price': ep_value,
                            'qty': qty_value,
                            'investment': ep_value * qty_value,
                            'current_value': ep_value * qty_value,  # Using entry price as current
                            'status': deal.get('status', 'UNKNOWN')
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error formatting deal: {e}")
                    continue

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

    def get_deals_by_symbol(self, user_id: int, symbol: str) -> List[Dict]:
        """
        Get all deals for a specific symbol using only real data
        Args:
            user_id: User ID
            symbol: Trading symbol
        Returns:
            List of deals for the symbol
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []

            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Query to get symbol-specific deals with real data only
            query = """
                SELECT trade_signal_id, symbol, qty, created_at, ep, pos, ed, status
                FROM public.user_deals 
                WHERE user_id = %s AND symbol = %s AND ep IS NOT NULL AND qty IS NOT NULL
                ORDER BY created_at DESC
            """

            cursor.execute(query, (user_id, symbol))
            deals = cursor.fetchall()

            conn.close()

            # Convert to list of dictionaries with real data only
            return [dict(deal) for deal in deals]

        except Exception as e:
            logger.error(f"Error getting deals for symbol {symbol}: {e}")
            return []