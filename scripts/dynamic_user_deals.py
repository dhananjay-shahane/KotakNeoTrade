"""
Dynamic User Deals Service
Creates and manages user-specific deal tables dynamically
"""
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DynamicUserDealsService:

    def __init__(self):
        # Use centralized database configuration
        from config.database_config import DatabaseConfig
        self.db_config_manager = DatabaseConfig()
        self.db_config = self.db_config_manager.get_config_dict()

    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config,
                                    cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

    def create_user_deals_table(self, username):
        """
        Create a dynamic user-specific deals table
        Table name format: {username}_deals
        """
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            table_name = f"{username}_deals"

            # Create table with updated structure (added date, exp, pr, pp columns)
            create_table_query = sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50),
                    trade_signal_id INTEGER,
                    symbol VARCHAR(50) NOT NULL,
                    date DATE,
                    qty INTEGER,
                    ep DECIMAL(10, 2),
                    pos VARCHAR(20) DEFAULT '1',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ed DATE,
                    exp DATE,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    target_price DECIMAL(10, 2),
                    stop_loss DECIMAL(10, 2),
                    pr VARCHAR(50),
                    pp VARCHAR(50)
                );
            """).format(sql.Identifier(table_name))

            cursor.execute(create_table_query)

            # Create indexes for better performance
            index_queries = [
                sql.SQL(
                    "CREATE INDEX IF NOT EXISTS {} ON {} (username);").format(
                        sql.Identifier(f"idx_{table_name}_username"),
                        sql.Identifier(table_name)),
                sql.SQL(
                    "CREATE INDEX IF NOT EXISTS {} ON {} (symbol);").format(
                        sql.Identifier(f"idx_{table_name}_symbol"),
                        sql.Identifier(table_name)),
                sql.SQL(
                    "CREATE INDEX IF NOT EXISTS {} ON {} (status);").format(
                        sql.Identifier(f"idx_{table_name}_status"),
                        sql.Identifier(table_name)),
            ]

            for index_query in index_queries:
                cursor.execute(index_query)

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Created user deals table: {table_name}")
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create user deals table for {username}: {e}")
            try:
                if 'conn' in locals() and conn is not None:
                    conn.rollback()
                    conn.close()
            except:
                pass
            return False

    def add_deal_to_user_table(self, username, deal_data):
        """
        Add a deal to user-specific deals table
        """
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            table_name = f"{username}_deals"

            # Check existing table structure to determine which columns exist
            check_columns_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """
            cursor.execute(check_columns_query, (table_name, ))
            existing_columns = [
                row['column_name'] for row in cursor.fetchall()
            ]

            # Prepare insert based on existing columns
            if 'username' in existing_columns:
                # New table structure with username column
                insert_query = sql.SQL("""
                    INSERT INTO {} (username, trade_signal_id, symbol, qty, ep, pos, status, target_price, stop_loss)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """).format(sql.Identifier(table_name))

                cursor.execute(insert_query,
                               (username, deal_data.get('trade_signal_id'),
                                deal_data.get('symbol'), deal_data.get('qty'),
                                deal_data.get('ep'), deal_data.get('pos'),
                                deal_data.get('status', 'ACTIVE'),
                                deal_data.get('target_price'),
                                deal_data.get('stop_loss')))
            else:
                # Old table structure without username column
                insert_query = sql.SQL("""
                    INSERT INTO {} (trade_signal_id, symbol, qty, ep, pos, status, target_price, stop_loss)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """).format(sql.Identifier(table_name))

                cursor.execute(
                    insert_query,
                    (deal_data.get('trade_signal_id'), deal_data.get('symbol'),
                     deal_data.get('qty'), deal_data.get('ep'),
                     deal_data.get('pos'), deal_data.get(
                         'status', 'ACTIVE'), deal_data.get('target_price'),
                     deal_data.get('stop_loss')))

            deal_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Added deal to {table_name}, ID: {deal_id}")
            return deal_id

        except Exception as e:
            logger.error(f"❌ Failed to add deal to {username} table: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return None

    def get_user_deals(self, username):
        """
        Get all deals from user-specific table
        """
        try:
            conn = self.get_connection()
            if not conn:
                return []

            cursor = conn.cursor()
            table_name = f"{username}_deals"

            # Check if table exists
            check_table_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """
            cursor.execute(check_table_query, (table_name, ))
            table_exists = cursor.fetchone()['exists']

            if not table_exists:
                logger.warning(f"Table {table_name} does not exist")
                cursor.close()
                conn.close()
                return []

            # Get deals from user table
            select_query = sql.SQL("""
                SELECT * FROM {} 
                ORDER BY created_at DESC;
            """).format(sql.Identifier(table_name))

            cursor.execute(select_query)
            deals = cursor.fetchall()

            cursor.close()
            conn.close()

            logger.info(f"✅ Retrieved {len(deals)} deals from {table_name}")
            return [dict(deal) for deal in deals]

        except Exception as e:
            logger.error(f"❌ Failed to get deals from {username} table: {e}")
            if 'conn' in locals() and conn:
                conn.close()
            return []

    def update_deal(self, username, deal_id, updates):
        """
        Update a deal in user-specific table
        """
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            table_name = f"{username}_deals"

            # Build update query dynamically
            set_clauses = []
            values = []

            for field, value in updates.items():
                if field not in ['id',
                                 'created_at']:  # Don't update these fields
                    set_clauses.append(
                        sql.SQL("{} = %s").format(sql.Identifier(field)))
                    values.append(value)

            if not set_clauses:
                logger.warning("No valid fields to update")
                cursor.close()
                conn.close()
                return False

            values.append(deal_id)  # For WHERE clause

            update_query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(set_clauses))

            cursor.execute(update_query, values)
            rows_affected = cursor.rowcount

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(
                f"✅ Updated deal {deal_id} in {table_name}, rows affected: {rows_affected}"
            )
            return rows_affected > 0

        except Exception as e:
            logger.error(
                f"❌ Failed to update deal {deal_id} in {username} table: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False

    def close_deal(self, username, deal_id):
        """
        Close a deal by setting status to CLOSED and exit date
        """
        updates = {'status': 'CLOSED', 'ed': datetime.now().date()}
        return self.update_deal(username, deal_id, updates)

    def table_exists(self, username):
        """
        Check if user deals table exists
        """
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            table_name = f"{username}_deals"

            check_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """
            cursor.execute(check_query, (table_name, ))
            exists = cursor.fetchone()['exists']

            cursor.close()
            conn.close()

            return exists

        except Exception as e:
            logger.error(
                f"❌ Failed to check if table exists for {username}: {e}")
            if 'conn' in locals() and conn:
                conn.close()
            return False


# Create global instance
dynamic_deals_service = DynamicUserDealsService()
