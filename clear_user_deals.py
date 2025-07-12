
#!/usr/bin/env python3
"""
Script to clear all data from user_deals table
"""
import logging
from core.database import get_db_connection
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_user_deals_table():
    """
    Clear all data from user_deals table
    """
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False

        with conn.cursor() as cursor:
            # Clear all data from user_deals table
            cursor.execute("TRUNCATE TABLE user_deals RESTART IDENTITY CASCADE;")
            conn.commit()
            
            logger.info("✅ Successfully cleared all data from user_deals table")
            
            # Verify the table is empty
            cursor.execute("SELECT COUNT(*) FROM user_deals;")
            count = cursor.fetchone()[0]
            logger.info(f"✅ Verified: user_deals table now has {count} rows")
            
            return True

    except Exception as e:
        logger.error(f"❌ Error clearing user_deals table: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🗑️  Clearing all data from user_deals table...")
    success = clear_user_deals_table()
    
    if success:
        print("✅ All data has been successfully removed from user_deals table")
    else:
        print("❌ Failed to clear user_deals table")
