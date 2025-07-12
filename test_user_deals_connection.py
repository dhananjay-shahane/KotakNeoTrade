#!/usr/bin/env python3
"""
Test connection to external database and check user_deals table
"""
import psycopg2
import psycopg2.extras
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_deals_connection():
    """Test connection to external database and check user_deals table"""
    db_config = {
        'host': "dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com",
        'database': "kotak_trading_db",
        'user': "kotak_trading_db_user",
        'password': "JRUlk8RutdgVcErSiUXqljDUdK8sBsYO",
        'port': 5432
    }
    
    try:
        connection = psycopg2.connect(**db_config)
        logger.info("✓ Connected to external database")
        
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Check if user_deals table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_deals')")
            table_exists = cursor.fetchone()[0]
            logger.info(f"user_deals table exists: {table_exists}")
            
            if table_exists:
                # Get count of rows
                cursor.execute("SELECT COUNT(*) as count FROM user_deals")
                row_count = cursor.fetchone()['count']
                logger.info(f"user_deals table has {row_count} rows")
                
                # If there are rows, get a sample
                if row_count > 0:
                    cursor.execute("SELECT * FROM user_deals LIMIT 5")
                    sample_data = cursor.fetchall()
                    logger.info(f"Sample data from user_deals:")
                    for row in sample_data:
                        logger.info(f"  {dict(row)}")
                else:
                    logger.info("user_deals table is empty")
                    
                # Check table structure
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_deals' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                logger.info(f"user_deals table structure:")
                for col in columns:
                    logger.info(f"  {col['column_name']}: {col['data_type']}")
            else:
                logger.error("user_deals table does not exist")
                
        connection.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    test_user_deals_connection()