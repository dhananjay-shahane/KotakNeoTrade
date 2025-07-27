
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_exit_date_column():
    """Add exit_date column to user_deals table if it doesn't exist"""
    try:
        # Database connection details
        database_url = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com:5432/kotak_trading_db"
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if exit_date column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user_deals' AND column_name='exit_date'
        """)
        
        if not cursor.fetchone():
            # Add exit_date column
            cursor.execute("""
                ALTER TABLE public.user_deals 
                ADD COLUMN exit_date DATE DEFAULT NULL
            """)
            conn.commit()
            logger.info("✓ Added exit_date column to user_deals table")
        else:
            logger.info("✓ exit_date column already exists in user_deals table")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding exit_date column: {e}")

if __name__ == "__main__":
    add_exit_date_column()
