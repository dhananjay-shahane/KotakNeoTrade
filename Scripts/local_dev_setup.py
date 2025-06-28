
import os
import subprocess
import json

def setup_local_dev():
    """Setup instructions for local development"""
    print("""
🔧 Local Development Setup (Optional)

If you want to develop locally while keeping production on Replit:

1. Install PostgreSQL locally:
   - macOS: brew install postgresql
   - Ubuntu: sudo apt-get install postgresql
   - Windows: Download from postgresql.org

2. Create local database:
   createdb kotak_neo_local

3. Set environment variable for local dev:
   export DATABASE_URL="postgresql://username:password@localhost:5432/kotak_neo_local"

4. Run migrations:
   python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"

5. Import data from backup (optional):
   python backup_manager.py import backups/users_backup_YYYYMMDD_HHMMSS.json

6. Run locally:
   python main.py

🚀 For production deployment, keep using Replit - it's optimized for your trading app!
""")

if __name__ == "__main__":
    setup_local_dev()
