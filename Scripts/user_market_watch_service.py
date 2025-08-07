"""
User Market Watch Service
Handles user-specific market watch lists using CSV files
Supports multiple named watch lists per user
File format: Each line = one watchlist, First column = list name, Following columns = symbols
"""
import os
import csv
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UserMarketWatchService:
    """Service for managing user market watch CSV files with multiple named lists"""
    
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
        return os.path.join(self.data_folder, f"{username}.csv")
    
    def create_user_csv_file(self, username: str) -> bool:
        """Create CSV file for user if it doesn't exist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if os.path.exists(filename):
                logger.info(f"✓ CSV file already exists for user: {username}")
                return True
            
            # Create empty file - no headers needed as each line is a watchlist
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                pass  # Create empty file
            
            logger.info(f"✓ Created CSV file for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating CSV file for user {username}: {e}")
            return False
    
    def create_watchlist(self, username: str, list_name: str) -> bool:
        """Create a new watchlist for user"""
        try:
            # Ensure CSV file exists
            if not self.create_user_csv_file(username):
                return False
            
            filename = self.get_user_csv_filename(username)
            
            # Check if list already exists
            if self.watchlist_exists(username, list_name):
                logger.warning(f"Watchlist '{list_name}' already exists for user {username}")
                return False
            
            # Add new watchlist line (just the list name)
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([list_name])
            
            logger.info(f"✓ Created watchlist '{list_name}' for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating watchlist '{list_name}' for user {username}: {e}")
            return False
    
    def add_symbol_to_watchlist(self, username: str, list_name: str, symbol: str) -> bool:
        """Add symbol to a specific watchlist"""
        try:
            # Ensure CSV file exists
            if not self.create_user_csv_file(username):
                return False
            
            filename = self.get_user_csv_filename(username)
            
            # Check if symbol already exists in this list
            if self.is_symbol_in_watchlist(username, list_name, symbol):
                logger.warning(f"Symbol {symbol} already in watchlist '{list_name}' for user {username}")
                return False
            
            # Read all lines
            lines = []
            list_found = False
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0] == list_name:
                        # Add symbol to this list
                        row.append(symbol.upper())
                        list_found = True
                    lines.append(row)
            
            if not list_found:
                # Create the list with the symbol
                lines.append([list_name, symbol.upper()])
            
            # Write back all lines
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(lines)
            
            logger.info(f"✓ Added symbol {symbol} to watchlist '{list_name}' for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding symbol {symbol} to watchlist '{list_name}' for user {username}: {e}")
            return False
    
    def remove_symbol_from_watchlist(self, username: str, list_name: str, symbol: str) -> bool:
        """Remove symbol from a specific watchlist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.warning(f"CSV file doesn't exist for user: {username}")
                return False
            
            # Read all lines and remove symbol from the specified list
            lines = []
            removed = False
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0] == list_name:
                        # Remove symbol from this list
                        symbols = [s for s in row[1:] if s.upper() != symbol.upper()]
                        if len(symbols) != len(row[1:]):
                            removed = True
                        if symbols:  # Keep list if it still has symbols
                            lines.append([list_name] + symbols)
                        else:  # Remove empty list
                            lines.append([list_name])
                    else:
                        lines.append(row)
            
            if not removed:
                logger.warning(f"Symbol {symbol} not found in watchlist '{list_name}' for user {username}")
                return False
            
            # Write back the filtered lines
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(lines)
            
            logger.info(f"✓ Removed symbol {symbol} from watchlist '{list_name}' for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing symbol {symbol} from watchlist '{list_name}' for user {username}: {e}")
            return False
    
    def get_user_watchlists(self, username: str) -> Dict[str, List[str]]:
        """Get all watchlists for user"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.info(f"CSV file doesn't exist for user: {username}, creating new one")
                self.create_user_csv_file(username)
                return {}
            
            watchlists = {}
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row:  # Skip empty lines
                        list_name = row[0]
                        symbols = [s.upper() for s in row[1:] if s.strip()]
                        watchlists[list_name] = symbols
            
            logger.info(f"✓ Retrieved {len(watchlists)} watchlists for user {username}")
            return watchlists
            
        except Exception as e:
            logger.error(f"❌ Error getting watchlists for user {username}: {e}")
            return {}
    
    def get_watchlist_symbols(self, username: str, list_name: str) -> List[str]:
        """Get symbols from a specific watchlist"""
        try:
            watchlists = self.get_user_watchlists(username)
            return watchlists.get(list_name, [])
        except Exception as e:
            logger.error(f"❌ Error getting symbols from watchlist '{list_name}' for user {username}: {e}")
            return []
    
    def get_user_watchlist(self, username: str) -> List[Dict]:
        """Get user's default watchlist in old format for backward compatibility"""
        try:
            # For backward compatibility, return 'My Watch List' or first list found
            watchlists = self.get_user_watchlists(username)
            
            # Look for default list names
            default_list = None
            if 'My Watch List' in watchlists:
                default_list = 'My Watch List'
            elif 'Default' in watchlists:
                default_list = 'Default'
            elif watchlists:
                default_list = next(iter(watchlists))
            
            if not default_list:
                return []
            
            symbols = watchlists[default_list]
            result = []
            for i, symbol in enumerate(symbols, 1):
                result.append({
                    'id': i,
                    'username': username,
                    'symbol': symbol.upper(),
                    'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            logger.info(f"✓ Retrieved {len(result)} symbols from default watchlist for user {username}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting default watchlist for user {username}: {e}")
            return []
    
    def is_symbol_in_watchlist(self, username: str, list_name: str, symbol: str) -> bool:
        """Check if symbol is in a specific watchlist"""
        try:
            symbols = self.get_watchlist_symbols(username, list_name)
            return symbol.upper() in [s.upper() for s in symbols]
        except Exception as e:
            logger.error(f"❌ Error checking if symbol {symbol} is in watchlist '{list_name}' for user {username}: {e}")
            return False
    
    def watchlist_exists(self, username: str, list_name: str) -> bool:
        """Check if a watchlist exists for user"""
        try:
            watchlists = self.get_user_watchlists(username)
            return list_name in watchlists
        except Exception as e:
            logger.error(f"❌ Error checking if watchlist '{list_name}' exists for user {username}: {e}")
            return False
    
    def delete_watchlist(self, username: str, list_name: str) -> bool:
        """Delete a watchlist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.warning(f"CSV file doesn't exist for user: {username}")
                return False
            
            # Read all lines except the one to delete
            lines = []
            deleted = False
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0] != list_name:
                        lines.append(row)
                    elif row and row[0] == list_name:
                        deleted = True
            
            if not deleted:
                logger.warning(f"Watchlist '{list_name}' not found for user {username}")
                return False
            
            # Write back the filtered lines
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(lines)
            
            logger.info(f"✓ Deleted watchlist '{list_name}' for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting watchlist '{list_name}' for user {username}: {e}")
            return False
    
    def edit_watchlist_name(self, username: str, old_name: str, new_name: str) -> bool:
        """Edit/rename a watchlist"""
        try:
            filename = self.get_user_csv_filename(username)
            
            if not os.path.exists(filename):
                logger.warning(f"CSV file doesn't exist for user: {username}")
                return False
            
            # Check if new name already exists
            if self.watchlist_exists(username, new_name):
                logger.warning(f"Watchlist '{new_name}' already exists for user {username}")
                return False
            
            # Read all lines and update the watchlist name
            lines = []
            found = False
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row and row[0] == old_name:
                        # Update the watchlist name
                        row[0] = new_name
                        found = True
                    lines.append(row)
            
            if not found:
                logger.warning(f"Watchlist '{old_name}' not found for user {username}")
                return False
            
            # Write back the updated lines
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(lines)
            
            logger.info(f"✓ Renamed watchlist '{old_name}' to '{new_name}' for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error editing watchlist name from '{old_name}' to '{new_name}' for user {username}: {e}")
            return False
    
    def get_watchlist_count(self, username: str, list_name: str = None) -> int:
        """Get count of symbols in a specific watchlist or total count"""
        try:
            if list_name:
                symbols = self.get_watchlist_symbols(username, list_name)
                return len(symbols)
            else:
                watchlists = self.get_user_watchlists(username)
                return sum(len(symbols) for symbols in watchlists.values())
        except Exception as e:
            logger.error(f"❌ Error getting watchlist count for user {username}: {e}")
            return 0
    
    def add_symbol_to_watchlist_old(self, username: str, symbol: str) -> bool:
        """Add symbol to default watchlist for backward compatibility"""
        # Use 'My Watch List' as default
        default_list_name = 'My Watch List'
        
        # Create the list if it doesn't exist
        if not self.watchlist_exists(username, default_list_name):
            self.create_watchlist(username, default_list_name)
        
        return self.add_symbol_to_watchlist(username, default_list_name, symbol)
    
    def remove_symbol_from_watchlist_old(self, username: str, symbol: str) -> bool:
        """Remove symbol from default watchlist for backward compatibility"""
        default_list_name = 'My Watch List'
        return self.remove_symbol_from_watchlist(username, default_list_name, symbol)