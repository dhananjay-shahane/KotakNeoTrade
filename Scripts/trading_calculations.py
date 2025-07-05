#!/usr/bin/env python3
"""
Trading Calculations Engine for Google Finance Market Data
Comprehensive calculation system for all trading metrics including P&L, targets, and performance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class TradingCalculations:
    """Comprehensive trading calculations engine"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config

    def calculate_all_metrics(self, trade_data: Dict) -> Dict:
        """Calculate all trading metrics for a trade record"""
        try:
            # Extract basic trade data
            symbol = trade_data.get('symbol', '').upper()
            qty = float(trade_data.get('qty', 0))
            ep = float(trade_data.get('ep', 0))  # Entry price
            cmp = float(trade_data.get('cmp', 0))  # Current market price
            pos = int(trade_data.get('pos', 1))  # Position: 1 for long, -1 for short

            # Basic calculations
            inv = qty * ep  # Investment amount
            current_value = qty * cmp  # Current value

            # P&L calculations
            if pos == 1:  # Long position
                pl = current_value - inv  # Profit/Loss
                chan_percent = ((cmp - ep) / ep) * 100 if ep > 0 else 0
            else:  # Short position
                pl = inv - current_value  # Profit/Loss (reversed for short)
                chan_percent = ((ep - cmp) / ep) * 100 if ep > 0 else 0

            # Target calculations (assume 10% target for now, can be customized)
            target_percent = 10.0
            if pos == 1:  # Long position
                tp = ep * (1 + target_percent / 100)  # Target price
            else:  # Short position
                tp = ep * (1 - target_percent / 100)  # Target price

            tva = qty * tp  # Target value amount
            tPr = tva - inv if pos == 1 else inv - tva  # Target profit

            # Performance calculations
            d30 = trade_data.get('d30', cmp)  # 30-day price
            d7 = trade_data.get('d7', cmp)   # 7-day price

            # Calculate 30-day and 7-day performance
            ch30 = ((cmp - d30) / d30) * 100 if d30 > 0 else 0
            ch7 = ((cmp - d7) / d7) * 100 if d7 > 0 else 0

            # Net calculations
            nt = cmp  # Net price (same as current price)

            # Calculate totals for symbol aggregation
            total_qty = self.get_total_quantity_for_symbol(symbol)
            total_invested = self.get_total_investment_for_symbol(symbol)

            # Format results
            calculated_data = {
                'symbol': symbol,
                'qty': qty,
                'ep': ep,
                'cmp': cmp,
                'pos': pos,
                'inv': round(inv, 2),
                'current_value': round(current_value, 2),
                'pl': round(pl, 2),
                'chan': f"{chan_percent:.2f}%",
                'tp': round(tp, 2),
                'tva': round(tva, 2),
                'tPr': round(tPr, 2),
                'd30': d30,
                'ch30': f"{ch30:.2f}%",
                'd7': d7,
                'ch7': f"{ch7:.2f}%",
                'nt': nt,
                'qt': total_qty,
                'iv': round(total_invested, 2),
                'ip': ep,  # Initial price (same as entry price)
                'updated_at': datetime.now().isoformat()
            }

            logger.info(f"✓ Calculated metrics for {symbol}: P&L=₹{pl:.2f}, Chan={chan_percent:.2f}%")
            return calculated_data

        except Exception as e:
            logger.error(f"❌ Error calculating metrics: {e}")
            return {}

    def get_total_quantity_for_symbol(self, symbol: str) -> float:
        """Get total quantity for a symbol across all trades"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT SUM(qty * pos) as total_qty 
                        FROM admin_trade_signals 
                        WHERE (symbol = %s OR etf = %s)
                        AND qty IS NOT NULL
                    """, (symbol, symbol))

                    result = cursor.fetchone()
                    return float(result[0]) if result and result[0] else 0.0

        except Exception as e:
            logger.error(f"Error getting total quantity for {symbol}: {e}")
            return 0.0

    def get_total_investment_for_symbol(self, symbol: str) -> float:
        """Get total investment value for a symbol across all trades"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT SUM(qty * ep) as total_investment 
                        FROM admin_trade_signals 
                        WHERE (symbol = %s OR etf = %s)
                        AND qty IS NOT NULL AND ep IS NOT NULL
                    """, (symbol, symbol))

                    result = cursor.fetchone()
                    return float(result[0]) if result and result[0] else 0.0

        except Exception as e:
            logger.error(f"Error getting total investment for {symbol}: {e}")
            return 0.0

    def calculate_exit_metrics(self, trade_data: Dict, exit_price: float) -> Dict:
        """Calculate exit metrics when a trade is closed"""
        try:
            qty = float(trade_data.get('qty', 0))
            ep = float(trade_data.get('ep', 0))
            pos = int(trade_data.get('pos', 1))

            # Exit calculations
            exit_value = qty * exit_price
            inv = qty * ep

            if pos == 1:  # Long position
                pr = exit_value - inv  # Profit on exit
                pp = ((exit_price - ep) / ep) * 100 if ep > 0 else 0
            else:  # Short position
                pr = inv - exit_value  # Profit on exit (reversed for short)
                pp = ((ep - exit_price) / ep) * 100 if ep > 0 else 0

            exit_data = {
                'ed': datetime.now().strftime('%Y-%m-%d'),  # Exit date
                'exp': exit_price,  # Exit price
                'pr': round(pr, 2),  # Profit on exit
                'pp': f"{pp:.2f}%",  # Profit percentage
                'exit_value': round(exit_value, 2)
            }

            logger.info(f"✓ Exit metrics calculated: Profit=₹{pr:.2f}, PP={pp:.2f}%")
            return exit_data

        except Exception as e:
            logger.error(f"❌ Error calculating exit metrics: {e}")
            return {}

    def update_database_with_calculations(self, symbol: str, calculated_data: Dict) -> int:
        """Update database with calculated trading metrics"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # Check which columns exist
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'admin_trade_signals'
                    """)
                    columns = [row[0] for row in cursor.fetchall()]

                    # Build update query with available columns - be more flexible with data types
                    update_fields = []
                    update_values = []

                    # Map calculated data to database columns with proper type handling
                    column_mapping = {
                        'cmp': 'cmp',
                        'inv': 'inv',
                        'pl': 'pl',
                        'chan': 'chan',
                        'tp': 'tp',
                        'tva': 'tva',
                        'tPr': 'tpr',
                        'd30': 'thirty',
                        'ch30': 'dh',
                        'd7': 'seven',
                        'ch7': 'ch',
                        'nt': 'nt',
                        'qt': 'qt',
                        'iv': 'iv',
                        'ip': 'ip'
                    }

                    for calc_field, db_column in column_mapping.items():
                        if db_column in columns and calc_field in calculated_data:
                            value = calculated_data[calc_field]

                            # Handle percentage fields specially
                            if calc_field in ['chan', 'ch30', 'ch7'] and isinstance(value, str):
                                update_fields.append(f"{db_column} = %s")
                                update_values.append(value)
                            # Handle numeric fields
                            elif calc_field in ['cmp', 'inv', 'pl', 'tp', 'tva', 'tPr', 'd30', 'd7', 'nt', 'iv', 'ip']:
                                update_fields.append(f"{db_column} = %s")
                                update_values.append(float(value) if value is not None else 0.0)
                            # Handle integer fields
                            elif calc_field in ['qt']:
                                update_fields.append(f"{db_column} = %s")
                                update_values.append(int(value) if value is not None else 0)
                            else:
                                update_fields.append(f"{db_column} = %s")
                                update_values.append(value)

                    # Add timestamp
                    if 'updated_at' in columns:
                        update_fields.append('updated_at = CURRENT_TIMESTAMP')

                    if update_fields:
                        # Add WHERE condition values
                        update_values.extend([symbol, symbol])

                        query = f"""
                            UPDATE admin_trade_signals 
                            SET {', '.join(update_fields)}
                            WHERE (symbol = %s OR etf = %s)
                        """

                        cursor.execute(query, update_values)
                        updated_rows = cursor.rowcount
                        conn.commit()

                        if updated_rows > 0:
                            logger.info(f"✓ Updated {updated_rows} records for {symbol} with calculated metrics")
                            logger.info(f"  Fields updated: {', '.join([f.split(' = ')[0] for f in update_fields if 'CURRENT_TIMESTAMP' not in f])}")
                        return updated_rows
                    else:
                        logger.warning(f"No matching columns found for {symbol}")
                        return 0

        except Exception as e:
            logger.error(f"❌ Error updating database for {symbol}: {e}")
            logger.error(f"Query: {query if 'query' in locals() else 'N/A'}")
            logger.error(f"Values: {update_values if 'update_values' in locals() else 'N/A'}")
            return 0

    def calculate_portfolio_summary(self) -> Dict:
        """Calculate overall portfolio summary metrics"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_trades,
                            SUM(qty * ep) as total_invested,
                            SUM(CASE WHEN pl IS NOT NULL THEN pl ELSE 0 END) as total_pl,
                            AVG(CASE WHEN pl IS NOT NULL THEN pl ELSE 0 END) as avg_pl,
                            COUNT(CASE WHEN pl > 0 THEN 1 END) as profitable_trades,
                            COUNT(CASE WHEN pl < 0 THEN 1 END) as losing_trades
                        FROM admin_trade_signals
                        WHERE qty IS NOT NULL AND ep IS NOT NULL
                    """)

                    result = cursor.fetchone()

                    if result:
                        total_trades = result['total_trades'] or 0
                        total_invested = float(result['total_invested'] or 0)
                        total_pl = float(result['total_pl'] or 0)
                        avg_pl = float(result['avg_pl'] or 0)
                        profitable_trades = result['profitable_trades'] or 0
                        losing_trades = result['losing_trades'] or 0

                        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                        roi = (total_pl / total_invested * 100) if total_invested > 0 else 0

                        summary = {
                            'total_trades': total_trades,
                            'total_invested': round(total_invested, 2),
                            'total_pl': round(total_pl, 2),
                            'avg_pl': round(avg_pl, 2),
                            'profitable_trades': profitable_trades,
                            'losing_trades': losing_trades,
                            'win_rate': round(win_rate, 2),
                            'roi': round(roi, 2),
                            'current_value': round(total_invested + total_pl, 2)
                        }

                        logger.info(f"✓ Portfolio summary: {total_trades} trades, ₹{total_pl:.2f} P&L, {win_rate:.1f}% win rate")
                        return summary
                    else:
                        return {}

        except Exception as e:
            logger.error(f"❌ Error calculating portfolio summary: {e}")
            return {}

    def _update_trade_record(self, cursor, trade_id: int, calculated_data: Dict):
        """Update individual trade record with calculated metrics"""
        try:
            # Check which columns exist in the table
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'admin_trade_signals'
            """)
            columns = [row[0] for row in cursor.fetchall()]

            # Build update query with available columns - be more conservative with updates
            update_fields = []
            update_values = []

            # Only update core fields that are most likely to exist
            core_mapping = {
                'cmp': 'cmp',
                'pl': 'pl',
                'inv': 'inv'
            }

            for calc_field, db_column in core_mapping.items():
                if db_column in columns and calc_field in calculated_data:
                    value = calculated_data[calc_field]
                    if value is not None:
                        update_fields.append(f"{db_column} = %s")
                        # Handle percentage strings by converting to numeric
                        if isinstance(value, str) and value.endswith('%'):
                            try:
                                numeric_value = float(value.replace('%', ''))
                                update_values.append(numeric_value)
                            except ValueError:
                                update_values.append(value)
                        else:
                            update_values.append(float(value) if isinstance(value, (int, float)) else value)

            # Add timestamp if column exists
            if 'updated_at' in columns:
                update_fields.append('updated_at = CURRENT_TIMESTAMP')

            if update_fields and update_values:
                update_values.append(trade_id)

                query = f"""
                    UPDATE admin_trade_signals 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """

                cursor.execute(query, update_values)
                logger.info(f"✓ Updated trade record {trade_id} with {len(update_fields)} fields")

        except Exception as e:
            logger.error(f"❌ Error updating trade record {trade_id}: {e}")
            # Log the specific query and values for debugging
            if 'query' in locals():
                logger.error(f"Query: {query}")
            if 'update_values' in locals():
                logger.error(f"Values: {update_values}")

    def calculate_trade_metrics(trade_data: Dict, db_config: Dict) -> Dict:
        """Main function to calculate all trading metrics"""
        calculator = TradingCalculations(db_config)
        return calculator.calculate_all_metrics(trade_data)

    def update_all_calculations(db_config: Dict) -> Dict:
        """Update calculations for all trades in the database"""
        calculator = TradingCalculations(db_config)

        try:
            with psycopg2.connect(**db_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get all trades
                    cursor.execute("""
                        SELECT * FROM admin_trade_signals 
                        WHERE qty IS NOT NULL AND ep IS NOT NULL
                    """)

                    trades = cursor.fetchall()
                    updated_count = 0

                    for trade in trades:
                        trade_dict = dict(trade)
                        calculated_data = calculator.calculate_all_metrics(trade_dict)

                        if calculated_data:
                            calculator._update_trade_record(cursor, trade_dict.get('id', -1), calculated_data)
                            updated_count += 1

                    conn.commit()

                # Get portfolio summary
                portfolio_summary = calculator.calculate_portfolio_summary()

                logger.info(f"✓ Updated calculations for {updated_count} trade records")
                return {
                    'updated_trades': updated_count,
                    'portfolio_summary': portfolio_summary,
                    'status': 'success'
                }

        except Exception as e:
            logger.error(f"❌ Error updating all calculations: {e}")
            return {
                'updated_trades': 0,
                'portfolio_summary': {},
                'status': 'error',
                'error': str(e)
            }

def calculate_trade_metrics(trade_data: Dict, db_config: Dict) -> Dict:
    """Main function to calculate all trading metrics"""
    calculator = TradingCalculations(db_config)
    return calculator.calculate_all_metrics(trade_data)

def update_all_calculations(db_config: Dict) -> Dict:
    """Update calculations for all trades in the database"""
    calculator = TradingCalculations(db_config)

    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all trades
                cursor.execute("""
                    SELECT * FROM admin_trade_signals 
                    WHERE qty IS NOT NULL AND ep IS NOT NULL
                """)

                trades = cursor.fetchall()
                updated_count = 0

                for trade in trades:
                    trade_dict = dict(trade)
                    calculated_data = calculator.calculate_all_metrics(trade_dict)

                    if calculated_data:
                        calculator._update_trade_record(cursor, trade_dict.get('id', -1), calculated_data)
                        updated_count += 1

                    conn.commit()

                # Get portfolio summary
                portfolio_summary = calculator.calculate_portfolio_summary()

                logger.info(f"✓ Updated calculations for {updated_count} trade records")
                return {
                    'updated_trades': updated_count,
                    'portfolio_summary': portfolio_summary,
                    'status': 'success'
                }

        except Exception as e:
            logger.error(f"❌ Error updating all calculations: {e}")
            return {
                'updated_trades': 0,
                'portfolio_summary': {},
                'status': 'error',
                'error': str(e)
            }