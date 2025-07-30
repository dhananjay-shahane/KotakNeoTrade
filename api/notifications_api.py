"""
Notifications API - Monitor admin_trade_signals for new entries
"""
import logging
from flask import Blueprint, jsonify, session
from datetime import datetime, timedelta
import traceback
import os
import sys

sys.path.append('Scripts')
try:
    from Scripts.external_db_service import DatabaseConnector
except ImportError:
    try:
        from external_db_service import DatabaseConnector
    except ImportError:
        from Scripts.db_connector import DatabaseConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notifications_api = Blueprint('notifications_api', __name__, url_prefix='/api')

class NotificationService:
    def __init__(self):
        self.db = DatabaseConnector()
        self.logger = logger

    def get_recent_signals(self, hours_ago=24):
        """Get recent trade signals added in the last X hours"""
        try:
            # Get signals from the last 24 hours
            query = """
            SELECT id, symbol, qty, pos, entry_price, created_at
            FROM public.admin_trade_signals 
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 10
            """
            
            result = self.db.execute_query(query, (hours_ago,))
            
            if result and isinstance(result, list) and len(result) > 0:
                notifications = []
                for signal in result:
                    # Format the notification message
                    action = "BUY" if signal.get('pos', '').upper() in ['LONG', 'BUY', '1'] else "SELL"
                    
                    notification = {
                        'id': signal.get('id'),
                        'symbol': signal.get('symbol', ''),
                        'qty': signal.get('qty', 0),
                        'action': action,
                        'entry_price': signal.get('entry_price', 0),
                        'created_at': signal.get('created_at'),
                        'message': f"New {action} signal for {signal.get('symbol', '')} - Qty: {signal.get('qty', 0)}"
                    }
                    notifications.append(notification)
                
                return notifications
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching recent signals: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []

    def get_notification_count(self, hours_ago=24):
        """Get count of new notifications"""
        try:
            query = """
            SELECT COUNT(*) as count
            FROM public.admin_trade_signals 
            WHERE created_at >= NOW() - INTERVAL '%s hours'
            """
            
            result = self.db.execute_query(query, (hours_ago,))
            
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get('count', 0)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting notification count: {str(e)}")
            return 0

# Initialize service
notification_service = NotificationService()

@notifications_api.route('/notifications', methods=['GET'])
def get_notifications():
    """Get recent trade signal notifications"""
    try:
        notifications = notification_service.get_recent_signals()
        count = notification_service.get_notification_count()
        
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