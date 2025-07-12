"""
Initialize Local Trading Data
Creates the necessary tables and initial data structure for fast ETF signals loading
"""

import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_admin_trade_signals_table():
    """Create admin_trade_signals table in local SQLite database"""
    try:
        db_path = "instance/trading_platform.db"
        
        # Ensure instance directory exists
        os.makedirs("instance", exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create admin_trade_signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_trade_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    etf TEXT,
                    symbol TEXT,
                    thirty REAL DEFAULT 0,
                    dh REAL DEFAULT 0,
                    date TEXT,
                    pos INTEGER DEFAULT 1,
                    qty INTEGER DEFAULT 1,
                    ep REAL DEFAULT 0,
                    cmp REAL DEFAULT 0,
                    chan REAL DEFAULT 0,
                    inv REAL DEFAULT 0,
                    tp REAL DEFAULT 0,
                    tva REAL DEFAULT 0,
                    tpr REAL DEFAULT 0,
                    pl REAL DEFAULT 0,
                    ed TEXT,
                    exp REAL DEFAULT 0,
                    pr REAL DEFAULT 0,
                    pp REAL DEFAULT 0,
                    iv REAL DEFAULT 0,
                    ip REAL DEFAULT 0,
                    nt TEXT,
                    qt REAL DEFAULT 0,
                    seven REAL DEFAULT 0,
                    ch REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check if table has data
            cursor.execute("SELECT COUNT(*) FROM admin_trade_signals")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Creating initial admin_trade_signals data structure")
                # Add one sample record to establish the structure
                cursor.execute('''
                    INSERT INTO admin_trade_signals 
                    (etf, symbol, date, pos, qty, ep, cmp, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'ETF_SIGNALS',
                    'TRADING_SIGNALS', 
                    datetime.now().strftime('%Y-%m-%d'),
                    1,
                    1,
                    0,
                    0,
                    datetime.now()
                ))
            
            conn.commit()
            logger.info(f"✅ admin_trade_signals table ready with {count + (1 if count == 0 else 0)} records")
            return True
            
    except Exception as e:
        logger.error(f"Error creating admin_trade_signals table: {e}")
        return False

def initialize_all_tables():
    """Initialize all required tables for the trading platform"""
    try:
        success = create_admin_trade_signals_table()
        if success:
            logger.info("✅ Local database initialization completed")
        return success
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    initialize_all_tables()