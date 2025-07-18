
"""Script to drop unwanted ETF tables from the database"""
from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_etf_tables():
    """Drop the unwanted ETF tables"""
    with app.app_context():
        try:
            # List of table names to drop
            tables_to_drop = [
                'etf_positions',
                'etf_signal_trades', 
                'etf_watchlist'
            ]
            
            for table_name in tables_to_drop:
                try:
                    # Check if table exists and drop it
                    result = db.engine.execute(f"DROP TABLE IF EXISTS {table_name}")
                    logger.info(f"✅ Dropped table: {table_name}")
                except Exception as e:
                    logger.error(f"Error dropping table {table_name}: {str(e)}")
            
            # Commit the changes
            db.session.commit()
            logger.info("✅ Successfully dropped all unwanted ETF tables")
            
        except Exception as e:
            logger.error(f"Error dropping ETF tables: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    drop_etf_tables()
    print("ETF table cleanup completed")
