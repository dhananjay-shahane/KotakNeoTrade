"""
Centralized Database Configuration for Kotak Neo Trading Platform
Single source of truth for all database connections and configurations
"""
import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Centralized database configuration and connection management"""
    
    def __init__(self):
        """Initialize database configuration from environment variables"""
        # SECURITY: Never hardcode credentials - always use environment variables
        # Check if we have either DATABASE_URL or individual DB credentials
        if not os.environ.get('DATABASE_URL') and not os.environ.get('DB_PASSWORD'):
            raise ValueError("Database credentials must be set in environment variables")
        
        self.config = {
            'host': os.environ.get('DB_HOST') or os.environ.get('PGHOST'),
            'database': os.environ.get('DB_NAME') or os.environ.get('PGDATABASE'),
            'user': os.environ.get('DB_USER') or os.environ.get('PGUSER'),
            'password': os.environ.get('DB_PASSWORD') or os.environ.get('PGPASSWORD'),
            'port': int(os.environ.get('DB_PORT') or os.environ.get('PGPORT', 5432))
        }
        
        # Build complete database URL
        self.database_url = os.environ.get('DATABASE_URL') or self._build_database_url()
        
    def _build_database_url(self) -> str:
        """Build database URL from individual components"""
        return (f"postgresql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}")
    
    def get_connection(self, cursor_factory=None) -> Optional[psycopg2.extensions.connection]:
        """
        Get a new database connection
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
            
        Returns:
            Database connection or None if failed
        """
        try:
            if cursor_factory:
                conn = psycopg2.connect(self.database_url, cursor_factory=cursor_factory)
            else:
                conn = psycopg2.connect(self.database_url)
            
            logger.debug("✓ Database connection established")
            return conn
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def get_dict_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Get connection with RealDictCursor factory for dictionary results"""
        return self.get_connection(cursor_factory=RealDictCursor)
    
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_results: bool = True) -> Optional[Any]:
        """
        Execute a query with automatic connection management
        
        Args:
            query: SQL query string
            params: Query parameters
            fetch_results: Whether to fetch and return results
            
        Returns:
            Query results or row count for non-SELECT queries
        """
        conn = None
        try:
            conn = self.get_dict_connection()
            if not conn:
                return None
                
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch_results and query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    logger.debug(f"Query returned {len(results)} rows")
                    return results
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                conn.close()
                logger.info("✅ Database connection test successful")
                return result[0] == 1
            return False
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get database configuration as dictionary"""
        return self.config.copy()
    
    def get_database_url(self) -> str:
        """Get complete database URL"""
        return self.database_url


class DatabaseConnector:
    """Backward compatible database connector using centralized config"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize with optional database URL (for backward compatibility)
        If no URL provided, uses centralized configuration
        """
        self.db_config = DatabaseConfig()
        self._connection = None
        # Use provided URL or fall back to centralized config
        self.database_url = database_url or self.db_config.get_database_url()
    
    def get_connection(self):
        """Get or create database connection"""
        if not self._connection or self._connection.closed:
            try:
                self._connection = psycopg2.connect(self.database_url)
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                return None
        return self._connection
    
    def execute_query(self, query: str, params: Optional[tuple] = None):
        """Execute query and return results as list of dictionaries"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                
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
    
    def disconnect(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
    
    def close(self):
        """Alias for disconnect for backward compatibility"""
        self.disconnect()


# Global database configuration instance
db_config = DatabaseConfig()

# Convenience functions for quick access
def get_db_connection(cursor_factory=None):
    """Get database connection using centralized config"""
    return db_config.get_connection(cursor_factory)

def get_db_dict_connection():
    """Get database connection with RealDictCursor"""
    return db_config.get_dict_connection()

def execute_db_query(query: str, params: Optional[tuple] = None, fetch_results: bool = True):
    """Execute database query using centralized config"""
    return db_config.execute_query(query, params, fetch_results)

def get_database_url():
    """Get database URL using centralized config"""
    return db_config.get_database_url()

def test_database_connection():
    """Test database connectivity"""
    return db_config.test_connection()