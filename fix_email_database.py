#!/usr/bin/env python3
"""
Fix Email Database Schema Issues
Add missing alternative_email column to user_email_settings table
"""
import sys
import os
sys.path.append('.')

from config.database_config import execute_db_query, get_db_connection

def fix_email_database_schema():
    """Fix missing alternative_email column in user_email_settings table"""
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Could not connect to database")
            return False
            
        with conn.cursor() as cursor:
            # Check if user_email_settings table exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'user_email_settings'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("📋 Creating user_email_settings table...")
                cursor.execute("""
                    CREATE TABLE user_email_settings (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        user_email VARCHAR(255),
                        alternative_email VARCHAR(255),
                        send_deals_in_mail BOOLEAN DEFAULT FALSE,
                        send_daily_change_data BOOLEAN DEFAULT FALSE,
                        subscription BOOLEAN DEFAULT FALSE,
                        daily_email_time TIME DEFAULT '09:00:00',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ user_email_settings table created successfully")
            else:
                # Check if alternative_email column exists
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user_email_settings' 
                    AND column_name = 'alternative_email'
                """)
                alt_email_exists = cursor.fetchone() is not None
                
                if not alt_email_exists:
                    print("📋 Adding missing alternative_email column...")
                    cursor.execute("""
                        ALTER TABLE user_email_settings 
                        ADD COLUMN IF NOT EXISTS alternative_email VARCHAR(255)
                    """)
                    print("✅ alternative_email column added successfully")
                else:
                    print("✅ alternative_email column already exists")
                    
            conn.commit()
            
            # Verify the fix
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_email_settings' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("\n📋 Current user_email_settings table structure:")
            for col in columns:
                print(f"   {col[0]} - {col[1]}")
                
        conn.close()
        print("\n✅ Email database schema fixed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing email database schema: {e}")
        return False

if __name__ == "__main__":
    fix_email_database_schema()