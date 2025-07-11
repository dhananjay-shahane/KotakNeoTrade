"""
Create user_deals table with all required columns for ETF signals integration
"""
import logging
from core.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_user_deals_table():
    """Create user_deals table with comprehensive structure"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False

        with conn.cursor() as cursor:
            # Create user_deals table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS user_deals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                entry_date DATE DEFAULT CURRENT_DATE,
                position_type VARCHAR(10) DEFAULT 'LONG',
                quantity INTEGER NOT NULL DEFAULT 1,
                entry_price DECIMAL(10,2) NOT NULL,
                current_price DECIMAL(10,2) DEFAULT 0,
                target_price DECIMAL(10,2) DEFAULT 0,
                stop_loss DECIMAL(10,2) DEFAULT 0,
                invested_amount DECIMAL(15,2) DEFAULT 0,
                current_value DECIMAL(15,2) DEFAULT 0,
                pnl_amount DECIMAL(15,2) DEFAULT 0,
                pnl_percent DECIMAL(10,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                deal_type VARCHAR(20) DEFAULT 'MANUAL',
                notes TEXT,
                tags VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- ETF Signal specific columns
                pos INTEGER DEFAULT 1,
                qty INTEGER DEFAULT 1,
                ep DECIMAL(10,2) DEFAULT 0,
                cmp DECIMAL(10,2) DEFAULT 0,
                tp DECIMAL(10,2) DEFAULT 0,
                inv DECIMAL(15,2) DEFAULT 0,
                pl DECIMAL(15,2) DEFAULT 0,
                chan_percent VARCHAR(20) DEFAULT '0%',
                signal_date VARCHAR(50),
                thirty VARCHAR(20) DEFAULT '0%',
                dh INTEGER DEFAULT 0,
                ed VARCHAR(50),
                exp VARCHAR(50),
                pr VARCHAR(50),
                pp VARCHAR(50),
                iv VARCHAR(50),
                ip VARCHAR(50),
                nt TEXT,
                qt VARCHAR(50),
                seven VARCHAR(20) DEFAULT '0%',
                ch VARCHAR(20) DEFAULT '0%',
                tva DECIMAL(15,2) DEFAULT 0,
                tpr DECIMAL(15,2) DEFAULT 0
            );
            """

            cursor.execute(create_table_query)

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_deals_symbol ON user_deals(symbol);",
                "CREATE INDEX IF NOT EXISTS idx_user_deals_status ON user_deals(status);",
                "CREATE INDEX IF NOT EXISTS idx_user_deals_created_at ON user_deals(created_at);"
            ]

            for index_query in indexes:
                cursor.execute(index_query)

            conn.commit()
            logger.info("✓ user_deals table created successfully with all required columns")
            return True

    except Exception as e:
        logger.error(f"Error creating user_deals table: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_user_deals_table()