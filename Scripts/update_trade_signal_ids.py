
#!/usr/bin/env python3
"""
Script to ensure all records in external database have unique trade_signal_id
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_trade_signal_ids():
    """Ensure all records have unique trade_signal_id in external database"""
    
    # Database connection parameters
    DB_HOST = os.getenv('SUPABASE_DB_HOST', 'aws-0-ap-south-1.pooler.supabase.com')
    DB_PORT = os.getenv('SUPABASE_DB_PORT', '6543')
    DB_NAME = os.getenv('SUPABASE_DB_NAME', 'postgres')
    DB_USER = os.getenv('SUPABASE_DB_USER', 'postgres.crlxmtjhvbnlezfgqvnl')
    DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD', 'Kaushik@123456')
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # Check if id column exists and is auto-incrementing
                cursor.execute("""
                    SELECT column_name, data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'admin_trade_signals' 
                    AND column_name = 'id'
                """)
                
                id_column = cursor.fetchone()
                
                if not id_column:
                    # Add id column if it doesn't exist
                    logger.info("Adding id column to admin_trade_signals table")
                    cursor.execute("""
                        ALTER TABLE admin_trade_signals 
                        ADD COLUMN id SERIAL PRIMARY KEY
                    """)
                else:
                    logger.info(f"ID column exists: {id_column}")
                
                # Update any records that might have null or duplicate IDs
                cursor.execute("""
                    SELECT COUNT(*) FROM admin_trade_signals WHERE id IS NULL
                """)
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    logger.info(f"Updating {null_count} records with null IDs")
                    cursor.execute("""
                        UPDATE admin_trade_signals 
                        SET id = nextval('admin_trade_signals_id_seq'::regclass)
                        WHERE id IS NULL
                    """)
                
                # Get total count of records
                cursor.execute("SELECT COUNT(*) FROM admin_trade_signals")
                total_records = cursor.fetchone()[0]
                
                logger.info(f"Total records in admin_trade_signals: {total_records}")
                
                # Verify uniqueness
                cursor.execute("""
                    SELECT COUNT(DISTINCT id) as unique_ids, COUNT(*) as total_records 
                    FROM admin_trade_signals
                """)
                
                result = cursor.fetchone()
                logger.info(f"Unique IDs: {result['unique_ids']}, Total records: {result['total_records']}")
                
                if result['unique_ids'] == result['total_records']:
                    logger.info("✓ All trade_signal_ids are unique")
                else:
                    logger.warning("⚠️ Some trade_signal_ids are not unique")
                
                conn.commit()
                
    except Exception as e:
        logger.error(f"Error updating trade signal IDs: {e}")
        raise

if __name__ == '__main__':
    update_trade_signal_ids()
    print("✅ Trade signal ID update completed!")
