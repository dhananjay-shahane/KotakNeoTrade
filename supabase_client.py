
import os
import logging
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import json

class SupabaseClient:
    """Supabase client for database operations and real-time subscriptions"""
    
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL')
        self.anon_key = os.environ.get('SUPABASE_ANON_KEY')
        self.service_role_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.url or not self.anon_key:
            logging.warning("Supabase credentials not found. Some features may not work.")
            self.supabase = None
            self.admin_client = None
        else:
            # Client for regular operations
            self.supabase: Client = create_client(self.url, self.anon_key)
            
            # Admin client with service role for admin operations
            if self.service_role_key:
                self.admin_client: Client = create_client(self.url, self.service_role_key)
            else:
                self.admin_client = self.supabase
                
            logging.info("✅ Supabase client initialized successfully")
    
    def is_connected(self) -> bool:
        """Check if Supabase is properly configured"""
        return self.supabase is not None
    
    # User Management
    def get_users(self) -> List[Dict]:
        """Get all users from Supabase"""
        try:
            if not self.supabase:
                return []
            
            response = self.supabase.table('users').select('*').execute()
            return response.data
        except Exception as e:
            logging.error(f"Error fetching users: {e}")
            return []
    
    def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Create a new user in Supabase"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return None
    
    def update_user(self, user_id: int, user_data: Dict) -> Optional[Dict]:
        """Update user in Supabase"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.table('users').update(user_data).eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error updating user: {e}")
            return None
    
    # ETF Signals Management
    def get_etf_signals(self, limit: int = 50) -> List[Dict]:
        """Get ETF signals from Supabase"""
        try:
            if not self.supabase:
                return []
            
            response = self.supabase.table('admin_trade_signals')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logging.error(f"Error fetching ETF signals: {e}")
            return []
    
    def create_etf_signal(self, signal_data: Dict) -> Optional[Dict]:
        """Create new ETF signal in Supabase"""
        try:
            if not self.admin_client:
                return None
            
            response = self.admin_client.table('admin_trade_signals').insert(signal_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error creating ETF signal: {e}")
            return None
    
    def update_etf_signal(self, signal_id: int, signal_data: Dict) -> Optional[Dict]:
        """Update ETF signal in Supabase"""
        try:
            if not self.admin_client:
                return None
            
            response = self.admin_client.table('admin_trade_signals')\
                .update(signal_data)\
                .eq('id', signal_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error updating ETF signal: {e}")
            return None
    
    # Real-time quotes
    def update_realtime_quote(self, symbol: str, quote_data: Dict) -> Optional[Dict]:
        """Update real-time quote in Supabase"""
        try:
            if not self.supabase:
                return None
            
            # Upsert operation - insert if not exists, update if exists
            response = self.supabase.table('realtime_quotes')\
                .upsert({
                    'symbol': symbol,
                    **quote_data
                })\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logging.error(f"Error updating realtime quote for {symbol}: {e}")
            return None
    
    def get_realtime_quotes(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """Get real-time quotes from Supabase"""
        try:
            if not self.supabase:
                return []
            
            query = self.supabase.table('realtime_quotes').select('*')
            
            if symbols:
                query = query.in_('symbol', symbols)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logging.error(f"Error fetching realtime quotes: {e}")
            return []
    
    # Real-time subscriptions
    def subscribe_to_signals(self, callback_function):
        """Subscribe to real-time changes in ETF signals"""
        try:
            if not self.supabase:
                return None
            
            def handle_changes(payload):
                callback_function(payload)
            
            subscription = self.supabase.table('admin_trade_signals')\
                .on('*', handle_changes)\
                .subscribe()
                
            return subscription
        except Exception as e:
            logging.error(f"Error subscribing to signals: {e}")
            return None
    
    def subscribe_to_quotes(self, callback_function):
        """Subscribe to real-time changes in quotes"""
        try:
            if not self.supabase:
                return None
            
            def handle_changes(payload):
                callback_function(payload)
            
            subscription = self.supabase.table('realtime_quotes')\
                .on('*', handle_changes)\
                .subscribe()
                
            return subscription
        except Exception as e:
            logging.error(f"Error subscribing to quotes: {e}")
            return None
    
    # Bulk operations
    def bulk_insert_quotes(self, quotes_data: List[Dict]) -> bool:
        """Bulk insert multiple quotes"""
        try:
            if not self.supabase or not quotes_data:
                return False
            
            response = self.supabase.table('realtime_quotes').upsert(quotes_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logging.error(f"Error bulk inserting quotes: {e}")
            return False
    
    def bulk_update_signals(self, signals_data: List[Dict]) -> bool:
        """Bulk update multiple signals"""
        try:
            if not self.admin_client or not signals_data:
                return False
            
            response = self.admin_client.table('admin_trade_signals').upsert(signals_data).execute()
            return len(response.data) > 0
        except Exception as e:
            logging.error(f"Error bulk updating signals: {e}")
            return False
    
    # Storage operations (for file uploads)
    def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> Optional[str]:
        """Upload file to Supabase storage"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.storage.from_(bucket).upload(file_path, file_data)
            return response.get('path') if response else None
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            return None
    
    def download_file(self, bucket: str, file_path: str) -> Optional[bytes]:
        """Download file from Supabase storage"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.storage.from_(bucket).download(file_path)
            return response
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            return None

# Global Supabase client instance
supabase_client = SupabaseClient()
