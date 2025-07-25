import logging
from typing import Optional
from psycopg2 import sql
import pandas as pd

logger = logging.getLogger(__name__)

class PriceFetcher:

    def __init__(self, db_connector):
        self.db = db_connector
        self.logger = logger

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in symbols schema"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'symbols' 
            AND table_name = %s
        )
        """
        result = self.db.execute_query(query, (table_name, ))
        return result and result[0]['exists']

    def get_cmp(self, symbol: str) -> Optional[float]:
        """
        Get current market price from _5min table
        Args:
            symbol: Stock symbol
        Returns:
            Last price or None if not available
        """
        try:
            table_name = f"{symbol.lower()}_5m"

            if not self.table_exists(table_name):
                self.logger.warning(f"5min table not found: {table_name}")
                return None

            query = sql.SQL("""
                SELECT close 
                FROM symbols.{} 
                ORDER BY datetime DESC 
                LIMIT 1
            """).format(sql.Identifier(table_name))

            result = self.db.execute_query(query)
            return float(result[0]['close']) if result else None

        except Exception as e:
            self.logger.error(f"Error fetching CMP: {str(e)}", exc_info=True)
            return None


class HistoricalFetcher:

    def __init__(self, db_connector):
        self.db = db_connector

    def table_exists(self, table_name: str) -> bool:
        query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'symbols' 
            AND table_name = %s
        )
        """
        result = self.db.execute_query(query, (table_name, ))
        return result and result[0]['exists']

    def get_offset_price(self, symbol: str, offset: int) -> Optional[float]:
        """
        Return close price for N trading days ago (offset=7 or 30).
        If not enough data, return None.
        """
        try:
            table_name = f"{symbol.lower()}_daily"
            if not self.table_exists(table_name):
                logger.warning(f"Table not found: symbols.{table_name}")
                return None

            # Count rows
            count_query = sql.SQL(
                "SELECT COUNT(*) as cnt FROM symbols.{}").format(
                    sql.Identifier(table_name))
            count_result = self.db.execute_query(count_query)
            row_count = count_result[0]['cnt'] if count_result else 0

            if row_count <= offset:
                return None  # Not enough rows

            # Get Nth previous close: 0 = latest, 1 = 1 trading day ago, ...
            price_query = sql.SQL("""
                SELECT close FROM symbols.{}
                ORDER BY datetime DESC
                OFFSET %s LIMIT 1
            """).format(sql.Identifier(table_name))
            result = self.db.execute_query(price_query, (offset, ))
            return float(result[0]['close']) if result else None
        except Exception as e:
            logger.error(f"Error fetching offset={offset} price: {e}",
                         exc_info=True)
            return None

    def get_latest_close(self, symbol: str) -> Optional[float]:
        """
        Return close price for latest available trading day.
        """
        try:
            table_name = f"{symbol.lower()}_daily"
            if not self.table_exists(table_name):
                logger.warning(f"Table not found: symbols.{table_name}")
                return None
            price_query = sql.SQL("""
                SELECT close FROM symbols.{}
                ORDER BY datetime DESC
                LIMIT 1
            """).format(sql.Identifier(table_name))
            result = self.db.execute_query(price_query)
            return float(result[0]['close']) if result else None
        except Exception as e:
            logger.error(f"Error fetching latest close price: {e}",
                         exc_info=True)
            return None


def try_percent(cmp_val, hist_val):
    """
    Calculate percent change if both are numbers, else '--'.
    """
    try:
        if (cmp_val is not None and hist_val is not None
                and isinstance(cmp_val, (int, float))
                and isinstance(hist_val, (int, float)) and hist_val != 0
                and not pd.isna(cmp_val) and not pd.isna(hist_val)):
            pct_change = (float(cmp_val) -
                          float(hist_val)) / float(hist_val) * 100
            return f"{pct_change:.2f}%"
        else:
            return '--'
    except Exception:
        return '--'