#!/usr/bin/env python3
"""
Fix Email Schema via API Endpoint
Creates an endpoint to fix the missing alternative_email column
"""
from flask import Flask, jsonify
import sys
import os

# Add path for imports
sys.path.append('.')

def fix_email_schema_endpoint():
    """Create a temporary endpoint to fix email schema"""
    try:
        from config.database_config import get_db_connection
        
        conn = get_db_connection()
        if not conn:
            return {"error": "Could not connect to database"}, 500
            
        with conn.cursor() as cursor:
            # Add missing alternative_email column
            cursor.execute("""
                ALTER TABLE user_email_settings 
                ADD COLUMN IF NOT EXISTS alternative_email VARCHAR(255)
            """)
            
            # Verify the column exists now
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user_email_settings' 
                AND column_name = 'alternative_email'
            """)
            alt_email_exists = cursor.fetchone() is not None
            
            conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "alternative_email column added successfully",
            "column_exists": alt_email_exists
        }
        
    except Exception as e:
        return {"error": f"Failed to fix email schema: {str(e)}"}, 500

if __name__ == "__main__":
    print("Testing email schema fix...")
    result = fix_email_schema_endpoint()
    print(result)