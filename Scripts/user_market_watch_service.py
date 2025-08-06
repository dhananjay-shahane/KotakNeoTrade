"""
User Market Watch Service
Handles user-specific market watch lists using CSV files
"""
import os
import csv
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UserMarketWatchService:
    """Service for managing user market watch CSV files"""
    
    def __init__(self):
        self.data_folder = "data"
        self.ensure_data_folder_exists()
    
    def ensure_data_folder_exists(self):
        """Create data folder if it doesn't exist"""
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logger.info(f"✓ Created data folder: {self.data_folder}")
    
    def get_user_csv_filename(self, username: str) -> str:
        """Get CSV filename for a user"""
        return os.path.join(self.data_folder, f"{username}_market_watch.csv")
    
    def create_user_csv_file(self, username: str) -> bool:
        """Create CSV file for user if it doesn't exist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if os.path.exists(filename):
                logger.info(f"✓ CSV file already exists for user: {username}")
                return True
            
            # Create CSV with headers
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'symbol', 'added_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            
            logger.info(f"✓ Created CSV file for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating CSV file for user {username}: {e}")
            return False
    
    def add_symbol_to_watchlist(self, username: str, symbol: str) -> bool:
        """Add symbol to user's watchlist"""
        try:
            # Ensure CSV file exists
            if not self.create_user_csv_file(username):
                return False
            
            filename = self.get_user_csv_filename(username)
            
            # Check if symbol already exists
            if self.is_symbol_in_watchlist(username, symbol):
                logger.warning(f"Symbol {symbol} already in watchlist for user {username}")
                return False
            
            # Get next ID
            next_id = self.get_next_id(username)
            
            # Add new row
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'symbol', 'added_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    'id': next_id,
                    'username': username,
                    'symbol': symbol.upper(),
                    'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            logger.info(f"✓ Added symbol {symbol} to watchlist for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding symbol {symbol} to watchlist for user {username}: {e}")
            return False
    
    def remove_symbol_from_watchlist(self, username: str, symbol: str) -> bool:
        """Remove symbol from user's watchlist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.warning(f"CSV file doesn't exist for user: {username}")
                return False
            
            # Read all rows except the one to remove
            rows_to_keep = []
            removed = False
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['symbol'].upper() != symbol.upper():
                        rows_to_keep.append(row)
                    else:
                        removed = True
            
            if not removed:
                logger.warning(f"Symbol {symbol} not found in watchlist for user {username}")
                return False
            
            # Write back the filtered rows
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'symbol', 'added_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows_to_keep)
            
            logger.info(f"✓ Removed symbol {symbol} from watchlist for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing symbol {symbol} from watchlist for user {username}: {e}")
            return False
    
    def get_user_watchlist(self, username: str) -> List[Dict]:
        """Get all symbols in user's watchlist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.info(f"CSV file doesn't exist for user: {username}, creating new one")
                self.create_user_csv_file(username)
                return []
            
            symbols = []
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    symbols.append({
                        'id': int(row['id']) if row['id'].isdigit() else 0,
                        'username': row['username'],
                        'symbol': row['symbol'].upper(),
                        'added_date': row['added_date']
                    })
            
            # Sort by ID
            symbols.sort(key=lambda x: x['id'])
            logger.info(f"✓ Retrieved {len(symbols)} symbols from watchlist for user {username}")
            return symbols
            
        except Exception as e:
            logger.error(f"❌ Error getting watchlist for user {username}: {e}")
            return []
    
    def is_symbol_in_watchlist(self, username: str, symbol: str) -> bool:
        """Check if symbol is in user's watchlist"""
        try:
            watchlist = self.get_user_watchlist(username)
            return any(item['symbol'].upper() == symbol.upper() for item in watchlist)
        except Exception as e:
            logger.error(f"❌ Error checking if symbol {symbol} is in watchlist for user {username}: {e}")
            return False
    
    def get_next_id(self, username: str) -> int:
        """Get next available ID for user's watchlist"""
        try:
            watchlist = self.get_user_watchlist(username)
            if not watchlist:
                return 1
            
            max_id = max(item['id'] for item in watchlist)
            return max_id + 1
            
        except Exception as e:
            logger.error(f"❌ Error getting next ID for user {username}: {e}")
            return 1
    
    def get_watchlist_count(self, username: str) -> int:
        """Get count of symbols in user's watchlist"""
        try:
            watchlist = self.get_user_watchlist(username)
            return len(watchlist)
        except Exception as e:
            logger.error(f"❌ Error getting watchlist count for user {username}: {e}")
            return 0