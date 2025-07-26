"""
Database connector for PriceFetcher integration
"""
import psycopg2
import psycopg2.extras
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector:
    def __init__(self, database_url):
        self.database_url = database_url
        self._connection = None
    
    def get_connection(self):
        if not self._connection or self._connection.closed:
            self._connection = psycopg2.connect(self.database_url)
        return self._connection
    
    def execute_query(self, query, params=None):
        """Execute query and return results as list of dictionaries"""
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                # Convert query to string if it's a Composed object
                query_str = str(query) if hasattr(query, '__str__') else query
                if query_str.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Database query error: {e}")
            if self._connection:
                self._connection.rollback()
            raise
    
    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()