
"""
Import trading signals from CSV files and send to users
"""
import pandas as pd
import json
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

class TradingSignalsImporter:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login_admin(self, username, password):
        """Login as admin user"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json={'username': username, 'password': password})
            if response.status_code == 200:
                logging.info("Admin login successful")
                return True
            else:
                logging.error(f"Login failed: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False
    
    def parse_csv_signals(self, csv_file_path):
        """Parse CSV file and extract trading signals"""
        try:
            df = pd.read_csv(csv_file_path)
            signals = []
            
            for _, row in df.iterrows():
                # Map CSV columns to signal data
                signal = {
                    'symbol': str(row.get('ETF', row.get('Symbol', ''))).strip(),
                    'signal_type': 'BUY' if row.get('Pos', 1) > 0 else 'SELL',
                    'entry_price': float(row.get('EP', 0)),
                    'current_price': float(row.get('CMP', row.get('EP', 0))),
                    'target_price': float(row.get('TP', 0)) if pd.notna(row.get('TP')) else None,
                    'quantity': int(row.get('Qty', 100)),
                    'change_percent': float(row.get('%Chan', 0)) if pd.notna(row.get('%Chan')) else None,
                    'invested_amount': float(row.get('Inv', 0)) if pd.notna(row.get('Inv')) else None,
                    'pnl': float(row.get('PL', 0)) if pd.notna(row.get('PL')) else None,
                    'signal_title': f"{'BUY' if row.get('Pos', 1) > 0 else 'SELL'} {str(row.get('ETF', row.get('Symbol', ''))).strip()}",
                    'signal_description': f"Position: {row.get('Pos', 1)}, Target: {row.get('TP', 'N/A')}, Volume: {row.get('Qty', 100)}"
                }
                
                # Add exchange info if available
                if 'Exchange' in row:
                    signal['exchange'] = str(row['Exchange']).strip()
                
                signals.append(signal)
            
            logging.info(f"Parsed {len(signals)} signals from CSV")
            return signals
            
        except Exception as e:
            logging.error(f"Error parsing CSV: {e}")
            return []
    
    def get_users_list(self):
        """Get list of users to send signals to"""
        try:
            response = self.session.get(f"{self.base_url}/api/admin/users")
            if response.status_code == 200:
                data = response.json()
                return data.get('users', [])
            else:
                logging.error(f"Failed to get users: {response.text}")
                return []
        except Exception as e:
            logging.error(f"Error getting users: {e}")
            return []
    
    def send_bulk_signals(self, signals, target_user_ids):
        """Send bulk signals to users"""
        try:
            payload = {
                'signals': signals,
                'target_user_ids': target_user_ids
            }
            
            response = self.session.post(f"{self.base_url}/api/admin/bulk-signal", 
                                       json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"Successfully sent signals: {data.get('message')}")
                return True
            else:
                logging.error(f"Failed to send signals: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending signals: {e}")
            return False
    
    def import_and_send(self, csv_file_path, admin_username, admin_password, target_user_uccs=None):
        """Complete import and send process"""
        try:
            # Login
            if not self.login_admin(admin_username, admin_password):
                return False
            
            # Parse signals
            signals = self.parse_csv_signals(csv_file_path)
            if not signals:
                logging.error("No signals to send")
                return False
            
            # Get users
            users = self.get_users_list()
            if not users:
                logging.error("No users found")
                return False
            
            # Filter target users if specified
            if target_user_uccs:
                target_users = [u for u in users if u['ucc'] in target_user_uccs]
            else:
                target_users = users
            
            target_user_ids = [u['id'] for u in target_users]
            
            if not target_user_ids:
                logging.error("No target users found")
                return False
            
            # Send signals
            success = self.send_bulk_signals(signals, target_user_ids)
            
            if success:
                logging.info(f"Successfully imported and sent {len(signals)} signals to {len(target_user_ids)} users")
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f"Import process error: {e}")
            return False

# Example usage
if __name__ == "__main__":
    importer = TradingSignalsImporter()
    
    # Example: Import from CSV and send to specific users
    csv_file = "attached_assets/INVESTMENTS - ETFS-V2_1750219398692.csv"  # Update with your CSV file path
    admin_user = "admin_ucc"  # Replace with actual admin UCC
    admin_pass = "admin_password"  # Replace with actual admin password
    target_uccs = ["USER001", "USER002"]  # Replace with target user UCCs, or None for all users
    
    success = importer.import_and_send(csv_file, admin_user, admin_pass, target_uccs)
    
    if success:
        print("✅ Trading signals imported and sent successfully!")
    else:
        print("❌ Failed to import and send trading signals")
