
import os
import json
from datetime import datetime
from scripts.models import db, User, UserSession, UserPreferences

class BackupManager:
    """Manage database backups and data export"""
    
    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def export_users_to_json(self):
        """Export user data to JSON format"""
        try:
            users = User.query.all()
            users_data = []
            
            for user in users:
                user_dict = user.to_dict()
                
                # Get user sessions
                sessions = UserSession.query.filter_by(user_id=user.id).all()
                user_dict['sessions'] = []
                for session in sessions:
                    session_dict = {
                        'session_id': session.session_id,
                        'created_at': session.created_at.isoformat() if session.created_at else None,
                        'expires_at': session.expires_at.isoformat() if session.expires_at else None,
                        'is_active': session.is_active
                    }
                    user_dict['sessions'].append(session_dict)
                
                # Get user preferences
                preferences = UserPreferences.query.filter_by(user_id=user.id).first()
                if preferences:
                    user_dict['preferences'] = {
                        'default_exchange': preferences.default_exchange,
                        'default_product_type': preferences.default_product_type,
                        'default_order_type': preferences.default_order_type,
                        'auto_refresh_interval': preferences.auto_refresh_interval,
                        'show_notifications': preferences.show_notifications,
                        'theme': preferences.theme,
                        'email_alerts': preferences.email_alerts,
                        'sms_alerts': preferences.sms_alerts
                    }
                
                users_data.append(user_dict)
            
            # Save to JSON file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.backup_dir}/users_backup_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(users_data, f, indent=2, default=str)
            
            print(f"✅ User data exported to {filename}")
            print(f"📊 Exported {len(users_data)} users")
            return filename
            
        except Exception as e:
            print(f"❌ Error exporting user data: {str(e)}")
            return None
    
    def import_users_from_json(self, filename):
        """Import user data from JSON backup"""
        try:
            with open(filename, 'r') as f:
                users_data = json.load(f)
            
            imported_count = 0
            for user_data in users_data:
                # Check if user already exists
                existing_user = User.query.filter_by(ucc=user_data['ucc']).first()
                if existing_user:
                    print(f"⚠️ User {user_data['ucc']} already exists, skipping...")
                    continue
                
                # Create new user
                user = User(
                    ucc=user_data['ucc'],
                    mobile_number=user_data['mobile_number'],
                    greeting_name=user_data.get('greeting_name'),
                    user_id=user_data.get('user_id'),
                    client_code=user_data.get('client_code'),
                    product_code=user_data.get('product_code'),
                    account_type=user_data.get('account_type'),
                    branch_code=user_data.get('branch_code'),
                    is_trial_account=user_data.get('is_trial_account', False),
                    access_token=user_data.get('access_token'),
                    session_token=user_data.get('session_token'),
                    sid=user_data.get('sid'),
                    rid=user_data.get('rid'),
                    is_active=user_data.get('is_active', True)
                )
                
                db.session.add(user)
                db.session.flush()  # Get the user ID
                
                # Import preferences if available
                if 'preferences' in user_data and user_data['preferences']:
                    prefs_data = user_data['preferences']
                    preferences = UserPreferences(
                        user_id=user.id,
                        default_exchange=prefs_data.get('default_exchange'),
                        default_product_type=prefs_data.get('default_product_type'),
                        default_order_type=prefs_data.get('default_order_type'),
                        auto_refresh_interval=prefs_data.get('auto_refresh_interval', 30),
                        show_notifications=prefs_data.get('show_notifications', True),
                        theme=prefs_data.get('theme', 'dark'),
                        email_alerts=prefs_data.get('email_alerts', False),
                        sms_alerts=prefs_data.get('sms_alerts', False)
                    )
                    db.session.add(preferences)
                
                imported_count += 1
            
            db.session.commit()
            print(f"✅ Imported {imported_count} users successfully")
            return imported_count
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error importing user data: {str(e)}")
            return 0
    
    def create_full_backup(self):
        """Create a complete backup of all data"""
        print("🔄 Creating full database backup...")
        
        # Export to JSON
        json_file = self.export_users_to_json()
        
        # Export database schema and data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create backup info file
        backup_info = {
            'timestamp': timestamp,
            'json_export': json_file,
            'database_url': os.environ.get('DATABASE_URL', 'Not available'),
            'backup_type': 'full'
        }
        
        info_file = f"{self.backup_dir}/backup_info_{timestamp}.json"
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"✅ Full backup created with info file: {info_file}")
        return backup_info

# CLI interface
if __name__ == "__main__":
    import sys
    from app import app
    
    backup_manager = BackupManager()
    
    with app.app_context():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "export":
                backup_manager.export_users_to_json()
            elif command == "import" and len(sys.argv) > 2:
                filename = sys.argv[2]
                backup_manager.import_users_from_json(filename)
            elif command == "full":
                backup_manager.create_full_backup()
            else:
                print("Usage: python backup_manager.py [export|import <filename>|full]")
        else:
            backup_manager.create_full_backup()
