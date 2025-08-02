
"""
Dynamic User Deals Service
Handles user-specific deals operations with dynamic table creation
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicUserDealsService:
    """Service for managing user-specific deals tables"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """Get database connection"""
        try:
            from config.database_config import get_db_connection
            return get_db_connection()
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            return None
    
    def table_exists(self, username):
        """Check if user deals table exists"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            with conn:
                with conn.cursor() as cursor:
                    table_name = f"{username}_deals"
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        );
                    """, (table_name,))
                    return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False
    
    def create_user_deals_table(self, username):
        """Create user-specific deals table"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            table_name = f"{username}_deals"
            
            with conn:
                with conn.cursor() as cursor:
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        trade_signal_id INTEGER,
                        symbol VARCHAR(50) NOT NULL,
                        qty INTEGER NOT NULL,
                        ep DECIMAL(10,2),
                        cmp DECIMAL(10,2),
                        pos INTEGER DEFAULT 1,
                        status VARCHAR(20) DEFAULT 'ACTIVE',
                        target_price DECIMAL(10,2),
                        stop_loss DECIMAL(10,2),
                        notes TEXT,
                        entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        exit_date TIMESTAMP,
                        exit_price DECIMAL(10,2),
                        pnl DECIMAL(10,2),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                    cursor.execute(create_table_query)
                    self.logger.info(f"Created table {table_name}")
                    return True
        except Exception as e:
            self.logger.error(f"Error creating user table: {e}")
            return False
    
    def get_user_deals(self, username):
        """Get all deals for a user"""
        try:
            if not self.table_exists(username):
                return []
            
            conn = self.get_connection()
            if not conn:
                return []
            
            table_name = f"{username}_deals"
            
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(f"""
                        SELECT * FROM {table_name} 
                        ORDER BY created_at DESC
                    """)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting user deals: {e}")
            return []
    
    def add_deal_to_user_table(self, username, deal_data):
        """Add a deal to user table"""
        try:
            if not self.table_exists(username):
                if not self.create_user_deals_table(username):
                    return None
            
            conn = self.get_connection()
            if not conn:
                return None
            
            table_name = f"{username}_deals"
            
            with conn:
                with conn.cursor() as cursor:
                    insert_query = f"""
                    INSERT INTO {table_name} 
                    (user_id, trade_signal_id, symbol, qty, ep, pos, status, target_price, stop_loss, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """
                    values = (
                        deal_data.get('user_id'),
                        deal_data.get('trade_signal_id'),
                        deal_data.get('symbol'),
                        deal_data.get('qty'),
                        deal_data.get('ep'),
                        deal_data.get('pos', 1),
                        deal_data.get('status', 'ACTIVE'),
                        deal_data.get('target_price'),
                        deal_data.get('stop_loss'),
                        deal_data.get('notes')
                    )
                    cursor.execute(insert_query, values)
                    deal_id = cursor.fetchone()[0]
                    self.logger.info(f"Added deal {deal_id} to {table_name}")
                    return deal_id
        except Exception as e:
            self.logger.error(f"Error adding deal to user table: {e}")
            return None


# Initialize service instance
dynamic_deals_service = DynamicUserDealsService()


# Helper functions for backwards compatibility
def get_user_deals_data(username):
    """Get user deals data"""
    return dynamic_deals_service.get_user_deals(username)


def exit_user_deal(username, deal_id, exit_data):
    """Exit a user deal"""
    try:
        if not dynamic_deals_service.table_exists(username):
            return False
        
        conn = dynamic_deals_service.get_connection()
        if not conn:
            return False
        
        table_name = f"{username}_deals"
        
        with conn:
            with conn.cursor() as cursor:
                update_query = f"""
                UPDATE {table_name} 
                SET status = 'EXITED', 
                    exit_date = %s, 
                    exit_price = %s,
                    pnl = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                values = (
                    datetime.now(),
                    exit_data.get('exit_price'),
                    exit_data.get('pnl'),
                    deal_id
                )
                cursor.execute(update_query, values)
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error exiting deal: {e}")
        return False


def add_user_deal(username, deal_data):
    """Add a user deal"""
    return dynamic_deals_service.add_deal_to_user_table(username, deal_data)


def update_user_deal(username, deal_id, update_data):
    """Update a user deal"""
    try:
        if not dynamic_deals_service.table_exists(username):
            return False
        
        conn = dynamic_deals_service.get_connection()
        if not conn:
            return False
        
        table_name = f"{username}_deals"
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for key, value in update_data.items():
            if key not in ['id', 'created_at']:  # Skip readonly fields
                set_clauses.append(f"{key} = %s")
                values.append(value)
        
        if not set_clauses:
            return False
        
        values.append(deal_id)
        
        with conn:
            with conn.cursor() as cursor:
                update_query = f"""
                UPDATE {table_name} 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                cursor.execute(update_query, values)
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating deal: {e}")
        return False


def delete_user_deal(username, deal_id):
    """Delete a user deal"""
    try:
        if not dynamic_deals_service.table_exists(username):
            return False
        
        conn = dynamic_deals_service.get_connection()
        if not conn:
            return False
        
        table_name = f"{username}_deals"
        
        with conn:
            with conn.cursor() as cursor:
                delete_query = f"DELETE FROM {table_name} WHERE id = %s"
                cursor.execute(delete_query, (deal_id,))
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting deal: {e}")
        return False
