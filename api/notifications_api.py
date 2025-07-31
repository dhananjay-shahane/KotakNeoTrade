
"""
Notifications API - Monitor admin_trade_signals for new entries
"""
import logging
from flask import Blueprint, jsonify, session
from datetime import datetime, timedelta
import traceback
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notifications_api = Blueprint('notifications_api', __name__, url_prefix='/api')

class NotificationService:
    def __init__(self):
        self.logger = logger
        self.database_url = os.environ.get('DATABASE_URL', 
            f"postgresql://{os.environ.get('DB_USER', 'kotak_trading_db_user')}:"
            f"{os.environ.get('DB_PASSWORD', 'JRUlk8RutdgVcErSiUXqljDUdK8sBsYO')}@"
            f"{os.environ.get('DB_HOST', 'dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com')}:"
            f"{os.environ.get('DB_PORT', '5432')}/"
            f"{os.environ.get('DB_NAME', 'kotak_trading_db')}")

    def get_db_connection(self):
        """Get database connection using the specified DATABASE_URL"""
        try:
            conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            return None

    def get_recent_signals(self, hours_ago=24):
        """Get recent trade signals added in the last X hours"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []

            with conn.cursor() as cursor:
                # Use the correct column names based on database schema
                query = """
                SELECT id, symbol, qty, pos, ep as entry_price, created_at
                FROM public.admin_trade_signals 
                WHERE created_at >= NOW() - INTERVAL %s
                ORDER BY created_at DESC
                LIMIT 10
                """
                
                cursor.execute(query, (f'{hours_ago} hours',))
                result = cursor.fetchall()
                
                if result:
                    notifications = []
                    for signal in result:
                        # Format the notification message
                        pos = signal.get('pos', 1)
                        action = "BUY" if pos == 1 else "SELL"
                        
                        notification = {
                            'id': signal.get('id'),
                            'symbol': signal.get('symbol', ''),
                            'qty': signal.get('qty', 0),
                            'action': action,
                            'entry_price': float(signal.get('entry_price', 0)) if signal.get('entry_price') else 0,
                            'created_at': signal.get('created_at').isoformat() if signal.get('created_at') else None,
                            'message': f"New {action} signal for {signal.get('symbol', '')} - Qty: {signal.get('qty', 0)}",
                            'time_ago': self.get_time_ago(signal.get('created_at'))
                        }
                        notifications.append(notification)
                    
                    conn.close()
                    return notifications
                
                conn.close()
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching recent signals: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []

    def get_notification_count(self, hours_ago=24):
        """Get count of new notifications"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return 0

            with conn.cursor() as cursor:
                query = """
                SELECT COUNT(*) as count
                FROM public.admin_trade_signals 
                WHERE created_at >= NOW() - INTERVAL %s
                """
                
                cursor.execute(query, (f'{hours_ago} hours',))
                result = cursor.fetchone()
                
                count = result.get('count', 0) if result else 0
                conn.close()
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting notification count: {str(e)}")
            return 0

    def get_time_ago(self, created_at):
        """Calculate time ago from created_at timestamp"""
        if not created_at:
            return "Unknown"
        
        try:
            now = datetime.now()
            if hasattr(created_at, 'replace'):
                # If it's a datetime object, make it timezone naive for comparison
                created_at = created_at.replace(tzinfo=None)
            
            diff = now - created_at
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except Exception as e:
            self.logger.error(f"Error calculating time ago: {str(e)}")
            return "Unknown"

# Initialize service
notification_service = NotificationService()

@notifications_api.route('/notifications', methods=['GET'])
def get_notifications():
    """Get recent trade signal notifications"""
    try:
        notifications = notification_service.get_recent_signals()
        count = notification_service.get_notification_count()
        
        logger.info(f"Retrieved {len(notifications)} notifications with count {count}")
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': count,
            'message': f'{count} new trade signals available' if count > 0 else 'No new notifications'
        })
        
    except Exception as e:
        logger.error(f"Error in get_notifications: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': 'Failed to fetch notifications',
            'notifications': [],
            'count': 0
        }), 500

@notifications_api.route('/notifications/count', methods=['GET'])
def get_notification_count():
    """Get count of new notifications"""
    try:
        count = notification_service.get_notification_count()
        
        logger.info(f"Notification count: {count}")
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        logger.error(f"Error in get_notification_count: {str(e)}")
        return jsonify({
            'success': False,
            'count': 0
        }), 500

@notifications_api.route('/notifications/clear', methods=['POST'])
def clear_notifications():
    """Clear notifications (mark as read)"""
    try:
        # For now, we just return success
        # In a real implementation, you might track read notifications per user
        return jsonify({
            'success': True,
            'message': 'Notifications cleared'
        })
        
    except Exception as e:
        logger.error(f"Error in clear_notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to clear notifications'
        }), 500
