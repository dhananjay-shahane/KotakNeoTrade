import logging
from typing import Optional
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

            # Quick table existence check with timeout
            if not self.table_exists(table_name):
                self.logger.warning(f"5min table not found: {table_name}")
                return None

            query = f"""
                SELECT close 
                FROM symbols.{table_name} 
                ORDER BY datetime DESC 
                LIMIT 1
            """

            # Use execute_query with timeout protection
            result = self.db.execute_query(query)
            if result and len(result) > 0 and 'close' in result[0]:
                close_val = result[0]['close']
                if close_val is not None:
                    return float(close_val)
            
            return None

        except Exception as e:
            self.logger.warning(f"CMP fetch error for {symbol}: {str(e)}")
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
                logger.warning(f"Daily table not found: symbols.{table_name}")
                return None

            # Get Nth previous close with simplified query
            price_query = f"""
                SELECT close FROM symbols.{table_name}
                ORDER BY datetime DESC
                OFFSET {offset} LIMIT 1
            """
            result = self.db.execute_query(price_query)
            
            if result and len(result) > 0 and 'close' in result[0]:
                close_val = result[0]['close']
                if close_val is not None:
                    return float(close_val)
            
            return None
            
        except Exception as e:
            logger.warning(f"Offset price fetch error for {symbol} (offset={offset}): {e}")
            return None

    def get_latest_close(self, symbol: str) -> Optional[float]:
        """
        Return close price for latest available trading day.
        """
        try:
            table_name = f"{symbol.lower()}_daily"
            if not self.table_exists(table_name):
                logger.warning(f"Daily table not found: symbols.{table_name}")
                return None
                
            price_query = f"""
                SELECT close FROM symbols.{table_name}
                ORDER BY datetime DESC
                LIMIT 1
            """
            result = self.db.execute_query(price_query)
            
            if result and len(result) > 0 and 'close' in result[0]:
                close_val = result[0]['close']
                if close_val is not None:
                    return float(close_val)
                    
            return None
            
        except Exception as e:
            logger.warning(f"Latest close fetch error for {symbol}: {e}")
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