
#!/usr/bin/env python3
"""
Create user_deals table if it doesn't exist
This ensures the add deal functionality works properly
"""

from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_user_deals_table():
    """Create user_deals table with all necessary columns"""
    try:
        with app.app_context():
            # Check if table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_deals'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("Creating user_deals table...")
                
                # Create the user_deals table
                db.session.execute(text("""
                    CREATE TABLE user_deals (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        symbol VARCHAR(50) NOT NULL,
                        trading_symbol VARCHAR(50),
                        exchange VARCHAR(20) DEFAULT 'NSE',
                        position_type VARCHAR(10) NOT NULL,
                        quantity INTEGER NOT NULL,
                        entry_price DECIMAL(10,2),
                        current_price DECIMAL(10,2),
                        target_price DECIMAL(10,2),
                        stop_loss DECIMAL(10,2),
                        invested_amount DECIMAL(15,2),
                        current_value DECIMAL(15,2),
                        pnl_amount DECIMAL(15,2),
                        pnl_percent DECIMAL(10,4),
                        status VARCHAR(20) DEFAULT 'ACTIVE',
                        deal_type VARCHAR(20) DEFAULT 'MANUAL',
                        notes TEXT,
                        tags VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        entry_date DATE,
                        exit_date DATE,
                        
                        -- ETF Signal specific columns
                        pos INTEGER,
                        qty INTEGER,
                        ep DECIMAL(10,2),
                        cmp DECIMAL(10,2),
                        tp DECIMAL(10,2),
                        inv DECIMAL(15,2),
                        pl DECIMAL(15,2),
                        chan_percent VARCHAR(20),
                        signal_date VARCHAR(50),
                        thirty VARCHAR(20),
                        dh INTEGER,
                        ed VARCHAR(50),
                        exp VARCHAR(50),
                        pr VARCHAR(50),
                        pp VARCHAR(50),
                        iv VARCHAR(50),
                        ip VARCHAR(50),
                        nt TEXT,
                        qt VARCHAR(50),
                        seven VARCHAR(20),
                        ch VARCHAR(20),
                        tva DECIMAL(15,2),
                        tpr DECIMAL(15,2)
                    );
                """))
                
                # Create indexes
                db.session.execute(text("CREATE INDEX idx_user_deals_user_id ON user_deals(user_id);"))
                db.session.execute(text("CREATE INDEX idx_user_deals_symbol ON user_deals(symbol);"))
                db.session.execute(text("CREATE INDEX idx_user_deals_status ON user_deals(status);"))
                
                db.session.commit()
                logger.info("✓ user_deals table created successfully")
                
            else:
                logger.info("✓ user_deals table already exists")
                
                # Check if we need to add missing columns
                try:
                    # Add ETF signal columns if they don't exist
                    etf_columns = [
                        'pos INTEGER',
                        'qty INTEGER', 
                        'ep DECIMAL(10,2)',
                        'cmp DECIMAL(10,2)',
                        'tp DECIMAL(10,2)',
                        'inv DECIMAL(15,2)',
                        'pl DECIMAL(15,2)',
                        'chan_percent VARCHAR(20)',
                        'signal_date VARCHAR(50)',
                        'thirty VARCHAR(20)',
                        'dh INTEGER',
                        'ed VARCHAR(50)',
                        'exp VARCHAR(50)',
                        'pr VARCHAR(50)',
                        'pp VARCHAR(50)',
                        'iv VARCHAR(50)',
                        'ip VARCHAR(50)',
                        'nt TEXT',
                        'qt VARCHAR(50)',
                        'seven VARCHAR(20)',
                        'ch VARCHAR(20)',
                        'tva DECIMAL(15,2)',
                        'tpr DECIMAL(15,2)'
                    ]
                    
                    for column_def in etf_columns:
                        column_name = column_def.split()[0]
                        try:
                            db.session.execute(text(f"ALTER TABLE user_deals ADD COLUMN {column_def};"))
                            logger.info(f"✓ Added column {column_name}")
                        except Exception as col_error:
                            if "already exists" in str(col_error).lower():
                                continue
                            else:
                                logger.warning(f"Could not add column {column_name}: {col_error}")
                    
                    db.session.commit()
                    
                except Exception as alter_error:
                    logger.warning(f"Some columns may already exist: {alter_error}")
                    db.session.rollback()
            
            return True
            
    except Exception as e:
        logger.error(f"Error creating user_deals table: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = create_user_deals_table()
    if success:
        print("✓ user_deals table is ready")
    else:
        print("❌ Failed to create user_deals table")
