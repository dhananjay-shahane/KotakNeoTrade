
import os
import subprocess
import logging
from datetime import datetime

def export_database():
    """Export database data using pg_dump"""
    try:
        # Get database URL using centralized config
        import sys
        sys.path.append('.')
        from config.database_config import get_database_url
        database_url = get_database_url()
        if not database_url:
            print("Database URL not found in centralized configuration")
            return False
        
        # Create export filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = f"database_export_{timestamp}.sql"
        
        # Run pg_dump
        print(f"Exporting database to {export_file}...")
        result = subprocess.run([
            'pg_dump', 
            database_url,
            '--no-password',
            '--format=plain',
            '--file', export_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database exported successfully to {export_file}")
            return True
        else:
            print(f"❌ Export failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during export: {str(e)}")
        return False

if __name__ == "__main__":
    export_database()
